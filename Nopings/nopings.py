import logging
from typing import Dict, Optional, Set

import discord
from discord.abc import Messageable
from redbot.core import Config, commands
from redbot.core.bot import Red

log = logging.getLogger("red.nopings")


class NoPings(commands.Cog):
    """Suppresses bot reply pings globally or for designated users."""

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.config: Config = Config.get_conf(
            self,
            identifier=8473920194,
            force_registration=True,
        )
        self.config.register_guild(enabled=False, blocked_users=[])

        # In-memory fast cache to prevent disk I/O on every bot send call
        self._cache: Dict[int, Dict[str, any]] = {}
        self._is_active: bool = False
        self._original_send = None
        self._patched_send = None

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """Comply with Red QA End User Data deletion requests."""
        all_guilds = await self.config.all_guilds()
        for guild_id, data in all_guilds.items():
            blocked = data.get("blocked_users", [])
            if user_id in blocked:
                blocked.remove(user_id)
                await self.config.guild_from_id(guild_id).blocked_users.set(blocked)
                if guild_id in self._cache:
                    self._cache[guild_id]["blocked"].discard(user_id)

    async def _build_cache(self) -> None:
        """Populate the in-memory cache for all guilds on cog load."""
        all_guilds = await self.config.all_guilds()
        for guild_id, data in all_guilds.items():
            self._cache[guild_id] = {
                "enabled": data.get("enabled", False),
                "blocked": set(data.get("blocked_users", [])),
            }

    async def cog_load(self) -> None:
        await self._build_cache()
        self._is_active = True

        if self._patched_send is not None:
            return

        original = Messageable.send
        cog = self

        async def send(messageable, content=None, **kwargs):
            if cog._is_active:
                try:
                    kwargs = await cog._suppress_reply_ping(messageable, kwargs)
                except Exception:
                    log.exception("Failed to evaluate no-ping settings. Sending message unaltered.")
            return await original(messageable, content, **kwargs)

        self._original_send = original
        self._patched_send = send
        Messageable.send = send

    def cog_unload(self) -> None:
        # Deactivate first to turn wrapper into an instant pass-through
        self._is_active = False

        # Cooperative unwrap: only detach if another cog didn't wrap over us
        if Messageable.send is self._patched_send:
            Messageable.send = self._original_send
            self._original_send = None
            self._patched_send = None

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

        guild_data = self._cache.get(guild.id)
        if not guild_data:
            return kwargs

        enabled: bool = guild_data.get("enabled", False)
        blocked_users: Set[int] = guild_data.get("blocked", set())

        if not enabled:
            if not blocked_users:
                return kwargs
            author_id = await self._reference_author_id(reference)
            if author_id is None or author_id not in blocked_users:
                return kwargs

        kwargs["mention_author"] = False

        # If an explicit AllowedMentions object was passed, disable replied_user on it as well
        allowed_mentions = kwargs.get("allowed_mentions")
        if isinstance(allowed_mentions, discord.AllowedMentions):
            kwargs["allowed_mentions"] = discord.AllowedMentions(
                everyone=allowed_mentions.everyone,
                roles=allowed_mentions.roles,
                users=allowed_mentions.users,
                replied_user=False,
            )

        return kwargs

    async def _reference_author_id(self, reference) -> Optional[int]:
        # 1. Direct message object
        author = getattr(reference, "author", None)
        if author is not None:
            return getattr(author, "id", None)

        # 2. Resolved message on a MessageReference (fast local lookup)
        resolved = getattr(reference, "resolved", None)
        if isinstance(resolved, discord.Message) and resolved.author is not None:
            return resolved.author.id

        # 3. Cached message reference
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

        # 4. Fallback HTTP fetch
        try:
            message = await channel.fetch_message(message_id)
            return message.author.id
        except (discord.HTTPException, discord.NotFound, discord.Forbidden):
            log.debug("Could not fetch referenced message %s for ping suppression.", message_id)
            return None

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

        # Update cache
        self._cache.setdefault(ctx.guild.id, {"enabled": False, "blocked": set()})["enabled"] = new_state

        try:
            await ctx.message.add_reaction("✅" if new_state else "❌")
        except discord.HTTPException:
            pass

        if new_state:
            text = "✅ Bot reply pings are now turned off for the entire server."
        else:
            text = "❌ Bot reply pings are back on for the server."

        await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())

    @nopings.command(name="add")
    @commands.admin_or_permissions(manage_guild=True)
    async def add_user(self, ctx: commands.Context, user: discord.Member):
        """Add a specific user so the bot will not ping when replying to them."""
        async with self.config.guild(ctx.guild).blocked_users() as blocked:
            if user.id in blocked:
                await ctx.send(
                    f"✅ **{user.display_name}** is already on the no-ping list!",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                return
            blocked.append(user.id)

        # Update cache
        self._cache.setdefault(ctx.guild.id, {"enabled": False, "blocked": set()})["blocked"].add(user.id)

        try:
            await ctx.message.add_reaction("✅")
        except discord.HTTPException:
            pass

        await ctx.send(
            f"✅ Added **{user.display_name}** to the no-ping list.",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @nopings.command(name="remove")
    @commands.admin_or_permissions(manage_guild=True)
    async def remove_user(self, ctx: commands.Context, user: discord.Member):
        """Remove a specific user from the no-ping bot reply list."""
        async with self.config.guild(ctx.guild).blocked_users() as blocked:
            if user.id not in blocked:
                await ctx.send(
                    f"❌ **{user.display_name}** was not on the no-ping list.",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                return
            blocked.remove(user.id)

        # Update cache
        if ctx.guild.id in self._cache:
            self._cache[ctx.guild.id]["blocked"].discard(user.id)

        try:
            await ctx.message.add_reaction("❌")
        except discord.HTTPException:
            pass

        await ctx.send(
            f"❌ Removed **{user.display_name}** from the no-ping list.",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @nopings.command(name="test")
    async def test_ping(self, ctx: commands.Context, target: Optional[discord.Member] = None):
        """Test bot reply ping status for yourself or another user."""
        target_user = target or ctx.author
        guild_data = self._cache.get(ctx.guild.id, {"enabled": False, "blocked": set()})

        enabled = guild_data["enabled"]
        is_user_blocked = target_user.id in guild_data["blocked"]

        if enabled:
            emoji = "✅"
            msg = (
                f"✅ Bot reply pings are **disabled** server-wide. "
                f"Bot replies to **{target_user.display_name}** will **not** ping."
            )
        elif is_user_blocked:
            emoji = "✅"
            msg = (
                f"✅ **{target_user.display_name}** is on the no-ping list. "
                "Bot replies to them will **not** ping."
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
        allowed = (
            discord.AllowedMentions.none()
            if should_suppress
            else discord.AllowedMentions(users=True, replied_user=True)
        )

        await ctx.reply(msg, allowed_mentions=allowed)
