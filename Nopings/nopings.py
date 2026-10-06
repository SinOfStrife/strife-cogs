import logging
from typing import Optional

import discord
from discord.abc import Messageable
from redbot.core import Config, commands

log = logging.getLogger("red.nopings")


class NoPings(commands.Cog):
    """Suppresses bot reply pings globally or for designated users."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8473920194, force_registration=True)
        self.config.register_guild(enabled=False, blocked_users=[])
        self._original_send = None
        self._patched_send = None

    async def cog_load(self) -> None:
        if self._patched_send is not None:
            return
        original = Messageable.send
        cog = self

        async def send(messageable, content=None, **kwargs):
            try:
                kwargs = await cog._suppress_reply_ping(messageable, kwargs)
            except Exception:
                log.exception("Failed to apply no-ping settings. Sending the message unchanged.")
            return await original(messageable, content, **kwargs)

        self._original_send = original
        self._patched_send = send
        Messageable.send = send

    async def cog_unload(self) -> None:
        if self._patched_send is not None and Messageable.send is self._patched_send:
            Messageable.send = self._original_send
        self._patched_send = None
        self._original_send = None

    async def _suppress_reply_ping(self, messageable, kwargs: dict) -> dict:
        reference = kwargs.get("reference")
        if reference is None:
            return kwargs

        guild = getattr(messageable, "guild", None)
        if guild is None:
            channel = getattr(messageable, "channel", None)
            guild = getattr(channel, "guild", None)
        if guild is None:
            return kwargs

        enabled = await self.config.guild(guild).enabled()
        blocked_users = await self.config.guild(guild).blocked_users()
        if not enabled:
            if not blocked_users:
                return kwargs
            author_id = await self._reference_author_id(reference)
            if author_id is None or author_id not in blocked_users:
                return kwargs

        kwargs["mention_author"] = False
        return kwargs

    async def _reference_author_id(self, reference) -> Optional[int]:
        author = getattr(reference, "author", None)
        if author is not None:
            return author.id

        cached = getattr(reference, "cached_message", None)
        if cached is not None and getattr(cached, "author", None) is not None:
            return cached.author.id

        message_id = getattr(reference, "message_id", None)
        if message_id is None:
            message_id = getattr(reference, "id", None)

        channel = getattr(cached, "channel", None) if cached is not None else None
        if channel is None:
            channel = getattr(reference, "channel", None)
        if channel is None:
            channel_id = getattr(reference, "channel_id", None)
            if channel_id is not None:
                channel = self.bot.get_channel(channel_id)
        if channel is None or message_id is None or not hasattr(channel, "fetch_message"):
            return None

        try:
            message = await channel.fetch_message(message_id)
        except discord.HTTPException:
            log.debug("Could not fetch referenced message %s to check the no-ping list.", message_id)
            return None
        return message.author.id

    @commands.group(name="nopings", invoke_without_command=True)
    @commands.guild_only()
    async def nopings(self, ctx: commands.Context):
        """Manage no-ping bot reply settings."""
        await ctx.send_help(ctx.command)

    @nopings.command(name="toggle")
    @commands.admin_or_permissions(manage_guild=True)
    async def toggle(self, ctx: commands.Context):
        """Toggle ping-less bot replies on or off for the server."""
        current = await self.config.guild(ctx.guild).enabled()
        new_state = not current
        await self.config.guild(ctx.guild).enabled.set(new_state)

        emoji = "✅" if new_state else "❌"
        try:
            await ctx.message.add_reaction(emoji)
        except discord.HTTPException:
            pass

        if new_state:
            text = "✅ Got it! Bot reply pings are turned off for the whole server now."
        else:
            text = "❌ Bot reply pings are back on for the server."

        await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())

    @nopings.command(name="add")
    @commands.admin_or_permissions(manage_guild=True)
    async def add_user(self, ctx: commands.Context, user: discord.Member):
        """Add a specific user so the bot won't ping when replying to them."""
        async with self.config.guild(ctx.guild).blocked_users() as blocked:
            if user.id in blocked:
                await ctx.send(
                    f"✅ **{user.display_name}** is already on the no-ping list!",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                return
            blocked.append(user.id)

        try:
            await ctx.message.add_reaction("✅")
        except discord.HTTPException:
            pass

        await ctx.send(
            f"✅ Added **{user.display_name}** to the list—I won't ping them when replying anymore.",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @nopings.command(name="remove")
    @commands.admin_or_permissions(manage_guild=True)
    async def remove_user(self, ctx: commands.Context, user: discord.Member):
        """Remove a specific user from the no-ping bot reply list."""
        async with self.config.guild(ctx.guild).blocked_users() as blocked:
            if user.id not in blocked:
                await ctx.send(
                    f"❌ **{user.display_name}** wasn't on the no-ping list anyway.",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                return
            blocked.remove(user.id)

        try:
            await ctx.message.add_reaction("❌")
        except discord.HTTPException:
            pass

        await ctx.send(
            f"❌ Removed **{user.display_name}** from the list. Normal bot reply pings will work for them again.",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @nopings.command(name="test")
    async def test_ping(self, ctx: commands.Context, target: discord.Member = None):
        """Test bot reply ping status for yourself or another user."""
        target_user = target or ctx.author
        enabled = await self.config.guild(ctx.guild).enabled()
        blocked_users = await self.config.guild(ctx.guild).blocked_users()
        is_user_blocked = target_user.id in blocked_users

        if enabled:
            emoji = "✅"
            msg = (
                f"✅ Bot reply pings are **disabled** server-wide. "
                f"Bot replies to **{target_user.display_name}** will **not** ping them."
            )
        elif is_user_blocked:
            emoji = "✅"
            msg = (
                f"✅ **{target_user.display_name}** is on the no-ping list. "
                "Bot replies to them will **not** ping them."
            )
        else:
            emoji = "❌"
            msg = (
                f"❌ No-ping mode is **off** for **{target_user.display_name}**. "
                "Bot replies to them **will** ping as normal."
            )

        try:
            await ctx.message.add_reaction(emoji)
        except discord.HTTPException:
            pass

        should_suppress = enabled or is_user_blocked
        if should_suppress:
            allowed = discord.AllowedMentions.none()
        else:
            allowed = discord.AllowedMentions(users=True, replied_user=True)

        await ctx.reply(msg, allowed_mentions=allowed)
