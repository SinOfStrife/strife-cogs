from __future__ import annotations

import logging
from typing import Any, Literal, Optional

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

log = logging.getLogger("red.strifecogs.nopings")


class NoPings(commands.Cog):
    """Prevents the bot from sending notification pings when replying to commands."""

    __version__ = "2.1.2"
    __author__ = ["SinOfStrife"]
    __red_end_user_data_statement__ = (
        "This cog stores Discord User IDs and Guild IDs to remember notification "
        "and reply ping preferences."
    )

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=948172635481, force_registration=True
        )

        self.config.register_user(nopings=False)
        self.config.register_guild(all_silent=False, protected_users=[])

        self._user_cache: set[int] = set()
        self._guild_cache: set[int] = set()
        self._guild_protected: dict[int, set[int]] = {}

    async def cog_load(self) -> None:
        """Pre-populate memory caches from config on load[span_5](start_span)[span_5](end_span)."""
        user_data = await self.config.all_users()
        self._user_cache = {
            user_id for user_id, data in user_data.items() if data.get("nopings", False)
        }

        guild_data = await self.config.all_guilds()
        self._guild_cache = {
            guild_id for guild_id, data in guild_data.items() if data.get("all_silent", False)
        }
        self._guild_protected = {
            guild_id: set(data.get("protected_users", []))
            for guild_id, data in guild_data.items()
        }

    def cog_unload(self) -> None:
        pass

    @commands.Cog.listener()
    async def on_command_invoke(self, ctx: commands.Context) -> None:
        """Intercept command context to ensure reply pings are suppressed when applicable[span_6](start_span)[span_6](end_span)."""
        author_id = ctx.author.id
        guild_id = ctx.guild.id if ctx.guild else None

        silence_user = author_id in self._user_cache
        silence_guild = guild_id is not None and guild_id in self._guild_cache
        silence_protected = (
            guild_id is not None
            and author_id in self._guild_protected.get(guild_id, set())
        )

        if silence_user or silence_guild or silence_protected:
            original_send = ctx.send

            async def wrapped_send(*args: Any, **kwargs: Any) -> discord.Message:
                if "reference" in kwargs or ctx.message.reference:
                    if "mention_author" not in kwargs:
                        kwargs["mention_author"] = False
                    
                    if "allowed_mentions" in kwargs and kwargs["allowed_mentions"] is not None:
                        am = kwargs["allowed_mentions"]
                        if isinstance(am, discord.AllowedMentions):
                            am.replied_user = False
                    else:
                        base = getattr(self.bot, "allowed_mentions", discord.AllowedMentions.default())
                        kwargs["allowed_mentions"] = discord.AllowedMentions(
                            everyone=base.everyone,
                            roles=base.roles,
                            users=base.users,
                            replied_user=False,
                        )
                return await original_send(*args, **kwargs)

            ctx.send = wrapped_send

    async def red_get_data_for_user(self, *, user_id: int) -> dict[str, Any]:
        """Return stored data for a user[span_7](start_span)[span_7](end_span)."""
        is_opted_in = user_id in self._user_cache
        protected_guilds = [
            str(guild_id)
            for guild_id, users in self._guild_protected.items()
            if user_id in users
        ]
        return {
            "personal_noping": is_opted_in,
            "force_silenced_in_guilds": protected_guilds,
        }

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ) -> None:
        """Delete stored user data on request across user and guild records[span_8](start_span)[span_8](end_span)."""
        await self.config.user_from_id(user_id).clear()
        self._user_cache.discard(user_id)

        for guild_id, users in list(self._guild_protected.items()):
            if user_id in users:
                users.discard(user_id)
                async with self.config.guild_from_id(guild_id).protected_users() as p_users:
                    if user_id in p_users:
                        p_users.remove(user_id)

    @commands.group(name="noping", aliases=["nopings"], invoke_without_command=True)
    async def noping(self, ctx: commands.Context) -> None:
        """Toggle whether the bot pings you when it replies to your commands[span_9](start_span)[span_9](end_span)."""
        current = ctx.author.id in self._user_cache
        new_state = not current

        if new_state:
            self._user_cache.add(ctx.author.id)
            await self.config.user(ctx.author).nopings.set(True)
            await ctx.send("Silent replies **enabled**: The bot will not ping you when replying.")
        else:
            self._user_cache.discard(ctx.author.id)
            await self.config.user(ctx.author).nopings.set(False)
            await ctx.send("Silent replies **disabled**: The bot will ping you normally when replying.")

    @noping.command(name="test")
    @commands.guild_only()
    async def noping_test(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        """Check if you or another member are currently silenced in this server[span_10](start_span)[span_10](end_span)."""
        target = member or ctx.author
        guild_id = ctx.guild.id

        is_personal = target.id in self._user_cache
        is_guild = guild_id in self._guild_cache
        is_force = target.id in self._guild_protected.get(guild_id, set())

        is_silenced = is_personal or is_guild or is_force

        if is_silenced:
            reasons = []
            if is_guild:
                reasons.append("server-wide setting is ON")
            if is_force:
                reasons.append("force-silenced by an admin in this server")
            if is_personal:
                reasons.append("personal preference is enabled")

            await ctx.send(
                f"🔇 **{target.display_name}** will **not** be pinged on replies ({', '.join(reasons)})."
            )
        else:
            await ctx.send(
                f"🔔 **{target.display_name}** will be pinged normally on replies."
            )

    @noping.group(name="set", aliases=["settings"], invoke_without_command=True)
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def noping_set(self, ctx: commands.Context) -> None:
        """Manage NoPings settings for this server[span_11](start_span)[span_11](end_span)."""
        await ctx.send_help()

    @noping_set.command(name="showsettings", aliases=["show"])
    async def noping_showsettings(self, ctx: commands.Context) -> None:
        """Display active NoPings settings for this server[span_12](start_span)[span_12](end_span)."""
        guild_id = ctx.guild.id
        all_silent = guild_id in self._guild_cache
        protected_ids = self._guild_protected.get(guild_id, set())

        if protected_ids:
            mentions = [f"<@{uid}>" for uid in protected_ids]
            members_text = ", ".join(mentions)
            if len(members_text) > 1000:
                shown = []
                current_len = 0
                for m in mentions:
                    if current_len + len(m) + 2 > 950:
                        break
                    shown.append(m)
                    current_len += len(m) + 2
                remaining = len(mentions) - len(shown)
                members_text = f"{', '.join(shown)} ... and {remaining} more"
        else:
            members_text = "None"

        can_embed = ctx.channel.permissions_for(ctx.me).embed_links
        if can_embed:
            embed = discord.Embed(
                title=f"NoPings Settings — {ctx.guild.name}",
                color=await ctx.embed_color(),
            )
            embed.add_field(
                name="Server-Wide Silent Replies",
                value="Enabled" if all_silent else "Disabled",
                inline=False,
            )
            embed.add_field(
                name=f"Force-Silenced Members ({len(protected_ids)})",
                value=members_text,
                inline=False,
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                f"**NoPings Settings — {ctx.guild.name}**\n"
                f"• Server-Wide Silent Replies: {'Enabled' if all_silent else 'Disabled'}\n"
                f"• Force-Silenced Members ({len(protected_ids)}): {members_text}"
            )

    @noping_set.command(name="toggle")
    async def noping_toggle(self, ctx: commands.Context) -> None:
        """Toggle server-wide silent replies on or off for everyone[span_13](start_span)[span_13](end_span)."""
        guild_id = ctx.guild.id
        current = guild_id in self._guild_cache
        new_state = not current

        if new_state:
            self._guild_cache.add(guild_id)
            await self.config.guild(ctx.guild).all_silent.set(True)
            await ctx.send("Server-wide silent replies **enabled**: The bot will not ping anyone in this server.")
        else:
            self._guild_cache.discard(guild_id)
            await self.config.guild(ctx.guild).all_silent.set(False)
            await ctx.send("Server-wide silent replies **disabled**: Standard user preferences now apply.")

    @noping_set.command(name="add")
    async def noping_add(self, ctx: commands.Context, member: discord.Member) -> None:
        """Force-add a member to this server's silent reply list[span_14](start_span)[span_14](end_span)."""
        guild_id = ctx.guild.id
        protected = self._guild_protected.setdefault(guild_id, set())

        if member.id in protected:
            await ctx.send(f"**{member.display_name}** is already force-silenced in this server.")
            return

        protected.add(member.id)
        async with self.config.guild(ctx.guild).protected_users() as users:
            if member.id not in users:
                users.append(member.id)

        await ctx.send(f"**{member.display_name}** has been force-added to this server's silent reply list.")

    @noping_set.command(name="remove")
    async def noping_remove(self, ctx: commands.Context, member: discord.Member) -> None:
        """Remove a member from this server's force-silenced list[span_15](start_span)[span_15](end_span)."""
        guild_id = ctx.guild.id
        protected = self._guild_protected.get(guild_id, set())

        if member.id not in protected:
            await ctx.send(f"**{member.display_name}** is not in this server's force-silenced list.")
            return

        protected.discard(member.id)
        async with self.config.guild(ctx.guild).protected_users() as users:
            if member.id in users:
                users.remove(member.id)

        await ctx.send(f"**{member.display_name}** has been removed from this server's force-silenced list.")


async def setup(bot: Red) -> None:
    await bot.add_cog(NoPings(bot))
