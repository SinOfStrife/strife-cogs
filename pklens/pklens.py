from __future__ import annotations

import asyncio
import time
from typing import Any, Literal, Optional
from urllib.parse import urlparse

import aiohttp
import discord
from redbot.core import app_commands, commands
from redbot.core.bot import Red

PK_API = "https://api.pluralkit.me/v2"
_TITLE_LIMIT = 256
_DESC_LIMIT = 4096
_FIELD_LIMIT = 1024
_MAX_CACHE_ITEMS = 500


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…" if limit > 1 else text[:limit]


def _member_label(member: dict[str, Any]) -> str:
    return member.get("display_name") or member.get("name") or "Unknown"


def _embed_color(color_hex: Optional[str]) -> discord.Color:
    if not color_hex:
        return discord.Color.default()
    try:
        return discord.Color(int(str(color_hex).removeprefix("#"), 16))
    except ValueError:
        return discord.Color.default()


def _is_valid_url(url: Any) -> bool:
    if not isinstance(url, str) or not (url.startswith("http://") or url.startswith("https://")):
        return False
    parsed = urlparse(url)
    return bool(parsed.netloc and parsed.scheme in {"http", "https"} and " " not in url)


class PKLens(commands.Cog):
    """A privacy-focused PluralKit inspector for Discord Context Menus and Slash Commands."""

    __version__ = "1.0.2"
    __author__ = ["SinOfStrife"]
    __red_end_user_data_statement__ = (
        "This cog does not store data. Looking up a user sends their "
        "Discord user ID to the PluralKit API at api.pluralkit.me."
    )

    def __init__(self, bot: Red) -> None:
        super().__init__()
        self.bot = bot
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {"User-Agent": "PKLens/1.0.2 (https://github.com/SinOfStrife/strife-cogs)"}

        # Cache: dict[endpoint, (timestamp, payload)]
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._cache_ttl = 60.0

        # Context Menus
        self.check_fronters_menu = app_commands.ContextMenu(
            name="fronters",
            callback=self.check_fronter_callback,
            allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
            allowed_contexts=app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True),
            extras={"red_force_enable": True},
        )
        self.view_profile_menu = app_commands.ContextMenu(
            name="profile",
            callback=self.view_profile_callback,
            allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
            allowed_contexts=app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True),
            extras={"red_force_enable": True},
        )

    async def cog_load(self) -> None:
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=20),
        )
        try:
            self.bot.tree.add_command(self.check_fronters_menu)
            self.bot.tree.add_command(self.view_profile_menu)
        except Exception:
            self._drop_menus()
            await self.session.close()
            self.session = None
            raise

    async def cog_unload(self) -> None:
        self._drop_menus()
        if self.session is not None and not self.session.closed:
            await self.session.close()
        self.session = None

    def _drop_menus(self) -> None:
        for menu in (self.check_fronters_menu, self.view_profile_menu):
            if self.bot.tree.get_command(menu.name, type=menu.type) is not None:
                self.bot.tree.remove_command(menu.name, type=menu.type)

    async def red_get_data_for_user(self, *, user_id: int) -> dict[str, Any]:
        return {}

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ) -> None:
        return

    def _save_to_cache(self, endpoint: str, payload: dict[str, Any], now: float) -> None:
        """Saves data to cache and removes oldest entries if cache exceeds limit."""
        if len(self._cache) >= _MAX_CACHE_ITEMS:
            oldest = min(self._cache.keys(), key=lambda k: self._cache[k][0])
            self._cache.pop(oldest, None)
        self._cache[endpoint] = (now, payload)

    async def fetch_pk_data(self, endpoint: str) -> dict[str, Any]:
        now = time.monotonic()
        if endpoint in self._cache:
            timestamp, cached_data = self._cache[endpoint]
            if now - timestamp < self._cache_ttl:
                return cached_data

        if self.session is None or self.session.closed:
            return {"error": "api_error"}

        try:
            async with self.session.get(f"{PK_API}{endpoint}") as resp:
                if resp.status == 404:
                    return {"error": "not_found"}
                if resp.status == 403:
                    return {"error": "private"}
                if resp.status == 429:
                    return {"error": "rate_limited"}
                if resp.status != 200:
                    return {"error": "api_error"}
                payload = await resp.json(content_type=None)
        except Exception:
            return {"error": "api_error"}

        if not isinstance(payload, dict):
            return {"error": "api_error"}

        self._save_to_cache(endpoint, payload, now)
        return payload

    async def _safe_send_embed(self, interaction: discord.Interaction, embed: discord.Embed) -> None:
        """Sends embed; strips thumbnail and retries if Discord rejects the image URL."""
        try:
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            if e.code == 50035 and embed.thumbnail:  # Invalid Form Body (bad URL)
                embed.set_thumbnail(url=None)
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                raise

    async def _send_pk_error(
        self,
        interaction: discord.Interaction,
        user: discord.User | discord.Member,
        data: dict[str, Any],
        kind: str,
    ) -> None:
        err = data.get("error", "api_error")
        if err == "not_found":
            msg = f"**{user.name}** is not registered with PluralKit or has a private profile."
        elif err == "private":
            msg = f"**{user.name}** has set their {kind} to **private**."
        elif err == "rate_limited":
            msg = "PluralKit is currently rate-limited. Please try again in a moment."
        else:
            msg = "An error occurred while contacting the PluralKit API."

        embed = discord.Embed(title="⚠️ Error", description=msg, color=discord.Color.red())
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def _reply_fronters(self, interaction: discord.Interaction, user: discord.User | discord.Member) -> None:
        data = await self.fetch_pk_data(f"/systems/{user.id}/fronters")
        if "error" in data:
            await self._send_pk_error(interaction, user, data, "fronters")
            return

        fronters = data.get("members") or []
        if not isinstance(fronters, list):
            await self._send_pk_error(interaction, user, {"error": "api_error"}, "fronters")
            return

        if not fronters:
            embed = discord.Embed(
                title=_clip(f"🟢 Current Fronters: {user.name}", _TITLE_LIMIT),
                description="No system members are currently fronting.",
                color=discord.Color.dark_grey(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        names = [_member_label(m) for m in fronters if isinstance(m, dict)]
        embed = discord.Embed(
            title=_clip(f"🟢 Current Fronters: {user.name}", _TITLE_LIMIT),
            description=_clip(", ".join(names) if names else "Unknown", _DESC_LIMIT),
            color=discord.Color.green(),
        )

        for member in fronters:
            if isinstance(member, dict):
                avatar = member.get("avatar_url")
                if _is_valid_url(avatar):
                    embed.set_thumbnail(url=avatar)
                    break

        await self._safe_send_embed(interaction, embed)

    async def _reply_profile(self, interaction: discord.Interaction, user: discord.User | discord.Member) -> None:
        data = await self.fetch_pk_data(f"/systems/{user.id}")
        if "error" in data:
            await self._send_pk_error(interaction, user, data, "system profile")
            return

        system_name = data.get("name") or user.name
        tag = data.get("tag")
        title = f"{system_name} [{tag}]" if tag else str(system_name)

        embed = discord.Embed(
            title=_clip(title, _TITLE_LIMIT),
            description=_clip(str(data.get("description") or "No description provided."), _DESC_LIMIT),
            color=_embed_color(data.get("color")),
        )
        embed.add_field(
            name="Pronouns",
            value=_clip(str(data.get("pronouns") or "Not specified."), _FIELD_LIMIT),
            inline=True,
        )

        avatar = data.get("avatar_url")
        if _is_valid_url(avatar):
            embed.set_thumbnail(url=avatar)

        await self._safe_send_embed(interaction, embed)

    # --- Slash Commands ---

    @app_commands.command(
        name="pklens",
        description="View info about PKLens.",
        extras={"red_force_enable": True},
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(public="Set to True to share info with the channel (default: False)")
    async def pklens_help(self, interaction: discord.Interaction, public: bool = False) -> None:
        can_embed = True
        if public and interaction.guild and interaction.channel:
            can_embed = interaction.channel.permissions_for(interaction.guild.me).embed_links

        if can_embed:
            embed = discord.Embed(
                title="🔍 PKLens",
                description="A privacy-focused tool to view public PluralKit system profiles and fronters.",
                color=discord.Color.from_str("#6b2598"),
            )
            embed.add_field(
                name="How to use",
                value="Use slash commands or right-click any user (`Apps` ➔ `fronters` or `profile`).",
                inline=False,
            )
            embed.set_footer(text="Lookups are private and ephemeral by default.")
            await interaction.response.send_message(embed=embed, ephemeral=not public)
        else:
            fallback = (
                "**🔍 PKLens**\n"
                "A privacy-focused tool to view public PluralKit profiles.\n"
                "Use `/pkfronters` or right-click any user (`Apps` ➔ `fronters`)."
            )
            await interaction.response.send_message(fallback, ephemeral=not public)

    @app_commands.command(
        name="pkfronters",
        description="Check who is currently fronting.",
        extras={"red_force_enable": True},
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def pkfronters_slash(self, interaction: discord.Interaction, user: discord.User) -> None:
        await interaction.response.defer(ephemeral=True)
        await self._reply_fronters(interaction, user)

    @app_commands.command(
        name="pkprofile",
        description="View a PluralKit system profile.",
        extras={"red_force_enable": True},
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def pkprofile_slash(self, interaction: discord.Interaction, user: discord.User) -> None:
        await interaction.response.defer(ephemeral=True)
        await self._reply_profile(interaction, user)

    async def check_fronter_callback(self, interaction: discord.Interaction, user: discord.User) -> None:
        await interaction.response.defer(ephemeral=True)
        await self._reply_fronters(interaction, user)

    async def view_profile_callback(self, interaction: discord.Interaction, user: discord.User) -> None:
        await interaction.response.defer(ephemeral=True)
        await self._reply_profile(interaction, user)