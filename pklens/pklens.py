from __future__ import annotations

import functools
import logging
from typing import Any, Literal

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

log = logging.getLogger("red.strifecogs.nopings")


class NoPings(commands.Cog):
    """Prevents the bot from sending notification pings when replying to commands."""

    __version__ = "1.0.1"
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

        # Opt-In default: Bot pings normally unless enabled
        self.config.register_user(nopings=False)
        self.config.register_guild(all_silent=False)

        # In-memory caches for O(1) lookups
        self._user_cache: set[int] = set()
        self._guild_cache: set[int] = set()

        self._original_context_send = getattr(
            commands.Context, "_nopings_original_send", commands.Context.send
        )

    async def cog_load(self) -> None:
        """Pre-populate cache and safely patch Context.send on load."""
        user_data = await self.config.all_users()
        self._user_cache = {
            user_id for user_id, data in user_data.items() if data.get("nopings", False)
        }

        guild_data = await self.config.all_guilds()
        self._guild_cache = {
            guild_id for guild_id, data in guild_data.items() if data.get("all_silent", False)
        }

        self._patch_context_send()

    def cog_unload(self) -> None:
        """Synchronously restore Context.send when unloaded."""
        commands.Context.send = self._original_context_send
        if hasattr(commands.Context, "_nopings_original_send"):
            delattr(commands.Context, "_nopings_original_send")
        log.info("NoPings unloaded: Restored default Context.send pipeline.")

    def _patch_context_send(self) -> None:
        """Intercept Context.send to handle reply mentions."""
        commands.Context._nopings_original_send = self._original_context_send
        original = self._original_context_send
        cog = self

        @functools.wraps(original)
        async def patched_send(ctx_self: commands.Context, *args: Any, **kwargs: Any) -> discord.Message:
            # Check strictly if this message is a reply
            has_reference = bool(kwargs.get("reference"))

            if has_reference:
                author_id = ctx_self.author.id
                guild_id = ctx_self.guild.id if ctx_self.guild else None

                silence_user = author_id in cog._user_cache
                silence_guild = guild_id is not None and guild_id in cog._guild_cache

                if silence_user or silence_guild:
                    if "mention_author" not in kwargs:
                        kwargs["mention_author"] = False

                    # Clone AllowedMentions to avoid mutating shared objects
                    if "allowed_mentions" in kwargs and kwargs["allowed_mentions"] is not None:
                        existing = kwargs["allowed_mentions"]
                        kwargs["allowed_mentions"] = discord.AllowedMentions(
                            everyone=existing.everyone,
                            roles=existing.roles,
                            users=existing.users,
                            replied_user=False,
                        )
                    elif "allowed_mentions" not in kwargs:
                        base_allowed = getattr(
                            cog.bot, "allowed_mentions", discord.AllowedMentions.default()
                        )
                        kwargs["allowed_mentions"] = discord.AllowedMentions(
                            everyone=base_allowed.everyone,
                            roles=base_allowed.roles,
                            users=base_allowed.users,
                            replied_user=False,
                        )

            return await original(ctx_self, *args, **kwargs)

        commands.Context.send = patched_send

    # --- GDPR / End-User Data Handlers ---

    async def red_get_data_for_user(self, *, user_id: int) -> dict[str, Any]:
        """Return stored data for a user."""
        is_silenced = user_id in self._user_cache
        return {"nopings": is_silenced}

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ) -> None:
        """Delete stored user data on request."""
        await self.config.user_from_id(user_id).clear()
        self._user_cache.discard(user_id)

    # --- Commands ---

    @commands.group(name="noping", invoke_without_command=True)
    async def noping(self, ctx: commands.Context) -> None:
        """Toggle whether the bot pings you when it replies to your commands."""
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

    @noping.command(name="server")
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def noping_server(self, ctx: commands.Context) -> None:
        """Toggle silent bot replies for everyone in this server."""
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