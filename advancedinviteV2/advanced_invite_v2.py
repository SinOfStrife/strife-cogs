# Copyright (c) 2021-2026 Jojo#7791, sinofstrife and Contributors
# Licensed under the MIT License

import logging
from typing import Any, Dict, Final, List, Optional, Union
import discord
from discord import app_commands
from discord.http import Route
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, humanize_number
from .utils import (
    ColorNoneConverter,
    InviteNoneConverter,
    NoneConverter,
    NoneStrict,
    ThumbnailConverter,
)

log = logging.getLogger("red.advancedinvitev2")


async def can_invite(ctx: commands.Context) -> bool:
    return await ctx.bot.is_owner(ctx.author) or await ctx.bot.is_invite_url_public()


_config_structure: Final[Dict[str, Any]] = {
    "custom_message": "Thanks for choosing {bot_name}!",
    "title": "Invite {bot_name}",
    "support_server": None,
    "footer": None,
    "accent_color": 5793266,
    "thumbnail": None,
    "custom_invite": None,
}


class AdvancedInviteV2(commands.Cog):
    """An advanced invite cog built using Discord Components V2 layout structures."""

    __authors__: Final[List[str]] = ["Jojo#7791", "sinofstrife"]
    __version__: Final[str] = "4.5.0"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self._invite_command: Optional[commands.Command] = self.bot.remove_command("invite")
        # Your unique cog storage ID
        self.config = Config.get_conf(self, 957289026195435520, force_registration=True)
        self.config.register_global(**_config_structure)

    async def red_delete_data_for_user(self, *, requester: Any, user_id: int) -> None:
        """Required by Red QA: This cog does not store any personal user data."""
        return

    def cog_unload(self) -> None:
        self.bot.remove_command("invite")
        if self._invite_command:
            self.bot.add_command(self._invite_command)

    @staticmethod
    def _humanize_list(data: List[str]) -> str:
        return humanize_list([f"`{i}`" for i in data])

    def format_help_for_context(self, ctx: commands.Context) -> str:
        plural = "" if len(self.__authors__) == 1 else "s"
        return (
            f"{super().format_help_for_context(ctx)}\n"
            f"**Author{plural}:** {self._humanize_list(self.__authors__)}\n"
            f"**Version:** `{self.__version__}`"
        )

    def _replace_placeholders(
        self,
        template: Optional[str],
        bot_name: str,
        guild_count_str: str,
        user_count_str: str,
    ) -> Optional[str]:
        """Replace all configured placeholders in any given string template."""
        if not template:
            return template

        replacements = {
            "{bot_name}": bot_name,
            "{botname}": bot_name,
            "{guild_count}": guild_count_str,
            "{guildcount}": guild_count_str,
            "{server_count}": guild_count_str,
            "{servercount}": guild_count_str,
            "{user_count}": user_count_str,
            "{usercount}": user_count_str,
            "{member_count}": user_count_str,
            "{membercount}": user_count_str,
        }

        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        return result

    async def _send_raw_v2_payload(self, channel_id: int, payload: Dict[str, Any]) -> None:
        """Send a Components V2 payload directly through Discord's REST route."""
        route = Route("POST", "/channels/{channel_id}/messages", channel_id=channel_id)
        await self.bot.http.request(route, json=payload)

    async def _build_invite_payload(self, me: Union[discord.ClientUser, discord.Member]) -> Dict[str, Any]:
        """Construct the Components V2 JSON message payload according to Discord specifications."""
        settings = await self.config.all()
        bot_name = me.name

        guild_count_raw = len(self.bot.guilds)
        total_members = sum(g.member_count for g in self.bot.guilds if g.member_count)
        user_count_raw = max(len(self.bot.users), total_members)

        guild_count_str = humanize_number(guild_count_raw)
        user_count_str = humanize_number(user_count_raw)

        title = self._replace_placeholders(
            settings["title"], bot_name, guild_count_str, user_count_str
        )
        message = self._replace_placeholders(
            settings["custom_message"], bot_name, guild_count_str, user_count_str
        )
        footer = self._replace_placeholders(
            settings.get("footer"), bot_name, guild_count_str, user_count_str
        )

        custom_invite = settings.get("custom_invite")
        if custom_invite:
            url = self._replace_placeholders(
                custom_invite, bot_name, guild_count_str, user_count_str
            )
        else:
            url = await self.bot.get_invite_url()

        support = settings.get("support_server")
        accent_color = settings.get("accent_color", 5793266)
        thumbnail = settings.get("thumbnail")

        buttons: List[Dict[str, Any]] = [
            {
                "type": 2,
                "style": 5,
                "label": f"Invite {bot_name}",
                "url": url,
            }
        ]
        if support:
            buttons.append({
                "type": 2,
                "style": 5,
                "label": "Support Server",
                "url": support,
            })

        action_row = {
            "type": 1,
            "components": buttons,
        }

        container_components: List[Dict[str, Any]] = []

        thumb_url: Optional[str] = None
        if thumbnail:
            if thumbnail.lower() in ("bot", "avatar", "me", "auto"):
                thumb_url = str(me.display_avatar.url)
            elif thumbnail.startswith(("http://", "https://")):
                thumb_url = thumbnail

        if thumb_url:
            container_components.append({
                "type": 9,
                "components": [
                    {
                        "type": 10,
                        "content": f"### {title}\n{message}",
                    }
                ],
                "accessory": {
                    "type": 11,
                    "media": {
                        "url": thumb_url,
                    },
                },
            })
        else:
            container_components.append({
                "type": 10,
                "content": f"### {title}\n{message}",
            })

        container_components.append({
            "type": 14,
            "divider": True,
            "spacing": 1,
        })
        container_components.append(action_row)

        if footer:
            container_components.append({
                "type": 14,
                "divider": True,
                "spacing": 1,
            })
            container_components.append({
                "type": 10,
                "content": f"-# {footer}",
            })

        container_component = {
            "type": 17,
            "accent_color": accent_color,
            "spoiler": False,
            "components": container_components,
        }

        return {
            "components": [container_component],
            "flags": 32768,
        }

    # ==========================================
    # PUBLIC SLASH COMMAND
    # ==========================================
    @app_commands.command(name="invite", description="Get the official invite link for the bot.")
    async def slash_invite(self, interaction: discord.Interaction) -> None:
        """Request the bot's invite link through Discord's slash command menu."""
        is_owner = await self.bot.is_owner(interaction.user)
        is_public = await self.bot.is_invite_url_public()

        if not (is_owner or is_public):
            await interaction.response.send_message(
                "The bot owner has disabled public invite links.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        me = interaction.guild.me if interaction.guild else self.bot.user
        payload = await self._build_invite_payload(me)

        try:
            dm_channel = interaction.user.dm_channel or await interaction.user.create_dm()
            await self._send_raw_v2_payload(dm_channel.id, payload)
            await interaction.followup.send("📬 I've sent you a DM with the invite!", ephemeral=True)

        except (discord.Forbidden, discord.HTTPException) as error:
            log.warning(
                "DM failed for slash user %s (%s): %s. Updating original interaction.",
                interaction.user,
                interaction.user.id,
                error,
            )
            try:
                app_id = interaction.application_id or self.bot.application_id
                route = Route(
                    "PATCH",
                    "/webhooks/{application_id}/{interaction_token}/messages/@original",
                    application_id=app_id,
                    interaction_token=interaction.token,
                )
                fallback_payload = dict(payload)
                # 64 (ephemeral/secret) + 32768 (components v2) = 32832
                fallback_payload["flags"] = 32832
                await self.bot.http.request(route, json=fallback_payload)
            except Exception as patch_err:
                log.exception("Failed to update original interaction with Components V2 for %s", interaction.user.id)
                await interaction.followup.send(
                    f"Failed to deliver invite layout: `{patch_err}`",
                    ephemeral=True,
                )

        except Exception as error:
            log.exception("Unexpected error in slash invite for %s", interaction.user.id)
            await interaction.followup.send(f"An unexpected error occurred: `{error}`", ephemeral=True)

    # ==========================================
    # PREFIX COMMANDS ([p]invite and settings)
    # ==========================================
    @commands.group(name="invite", usage="", invoke_without_command=True)
    @commands.check(can_invite)
    async def invite(self, ctx: commands.Context) -> None:
        """Invite [botname] to your server (delivered to your DMs)!

        If your direct messages are closed, the invite will be sent directly here in the channel.
        """
        me = ctx.me or self.bot.user
        payload = await self._build_invite_payload(me)

        try:
            dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
            await self._send_raw_v2_payload(dm_channel.id, payload)

            msg = await ctx.send(f"{ctx.author.mention}, I've sent you a DM with the invite!")
            try:
                await msg.delete(delay=10)
            except Exception:
                pass

        except (discord.Forbidden, discord.HTTPException) as error:
            log.warning("DM delivery failed for %s (%s): %s. Attempting fallback.", ctx.author, ctx.author.id, error)

            fallback_components = [
                {
                    "type": 10,
                    "content": f"⚠️ {ctx.author.mention}, I couldn't send you a DM (your DMs might be closed). Here is the invite:",
                }
            ] + payload["components"]

            fallback_payload = {
                "components": fallback_components,
                "flags": 32768,
            }

            try:
                await self._send_raw_v2_payload(ctx.channel.id, fallback_payload)
            except Exception as channel_err:
                log.exception("Failed to send invite fallback in channel %s", ctx.channel.id)
                await ctx.send(f"Failed to deliver invite layout: `{channel_err}`")

        except Exception as error:
            log.exception("Unexpected error in invite command for user %s", ctx.author.id)
            await ctx.send(f"Failed to send invite: `{error}`")

    @invite.group(name="settings", aliases=("set",), invoke_without_command=True)
    @commands.is_owner()
    async def invite_settings(self, ctx: commands.Context) -> None:
        """Manage all configuration settings for the invite command.

        **Prefix Only:** All settings are managed exclusively via prefix commands.
        Run `[p]invite set showsettings` to view all current values.
        """
        await ctx.send_help()

    @invite_settings.command(name="url", aliases=("boturl", "botinvite", "customurl", "custominvite", "link"))
    async def invite_url(
        self, ctx: commands.Context, *, invite: Union[InviteNoneConverter, NoneConverter]
    ) -> None:
        """Set a custom bot invite URL for the main invite button.

        If set to `none` or `default`, it falls back to the bot's default generated invite URL.

        **Usage:**
        • `[p]invite set url https://discord.com/oauth2/authorize?client_id=123...`
        • `[p]invite set url none` (resets back to the bot's default invite)
        • `[p]invite set url default`
        """
        try:
            invite_url = getattr(invite, "url", invite)
            if invite_url and isinstance(invite_url, str) and invite_url.lower() in ("default", "none", "reset"):
                invite_url = None

            if not invite_url:
                await self.config.custom_invite.set(None)
                default_url = await self.bot.get_invite_url()
                await ctx.send(
                    f"The main invite button has been reset to the bot's default generated invite URL:\n<{default_url}>"
                )
                return

            if isinstance(invite_url, str) and not (invite_url.startswith("http://") or invite_url.startswith("https://")):
                invite_url = f"https://{invite_url}"

            await self.config.custom_invite.set(str(invite_url))
            await ctx.send(f"The main invite button URL has been set to: <{invite_url}>.")
        except Exception as error:
            log.exception("Failed to update custom invite URL setting.")
            await ctx.send(f"Failed to update custom invite URL: `{error}`")

    @invite_settings.command(name="support")
    async def invite_support(self, ctx: commands.Context, invite: InviteNoneConverter) -> None:
        """Set the support server invite button.

        **Usage:**
        • `[p]invite set support https://discord.gg/yourinvite`
        • `[p]invite set support none` (removes the button completely)
        """
        try:
            invite_url = getattr(invite, "url", invite)
            set_reset = f"set to: <{invite_url}>." if invite_url else "removed."
            await self.config.support_server.set(invite_url)
            await ctx.send(f"The support server button has been {set_reset}")
        except Exception as error:
            log.exception("Failed to update support server setting.")
            await ctx.send(f"Failed to update support server: `{error}`")

    @invite_settings.command(name="message")
    async def invite_message(self, ctx: commands.Context, *, message: NoneStrict) -> None:
        """Set the body text of the invite layout.

        **Live Placeholders:**
        • `{bot_name}`: The bot's name
        • `{guild_count}`: Number of servers the bot is in
        • `{user_count}`: Total users served

        **Usage:**
        • `[p]invite set message Thanks for choosing {bot_name}! Serving {user_count} users across {guild_count} servers.`
        • `[p]invite set message default` (resets to default)
        """
        try:
            if message is None:
                message = _config_structure["custom_message"]
                await self.config.custom_message.set(message)
                await ctx.send("The invite message has been reset to default.")
            else:
                if len(message) > 1500:
                    await ctx.send("The message cannot exceed 1500 characters.")
                    return
                await self.config.custom_message.set(message)
                await ctx.send("The invite message has been updated.")
        except Exception as error:
            log.exception("Failed to update message setting.")
            await ctx.send(f"Failed to update message: `{error}`")

    @invite_settings.command(name="title")
    async def invite_title(self, ctx: commands.Context, *, title: NoneStrict) -> None:
        """Set the title heading of the invite layout.

        **Live Placeholders:**
        • `{bot_name}`: The bot's name
        • `{guild_count}`: Number of servers the bot is in
        • `{user_count}`: Total users served

        **Usage:**
        • `[p]invite set title Add {bot_name} to your server!`
        • `[p]invite set title default` (resets to default)
        """
        try:
            if title is None:
                title = _config_structure["title"]
                await self.config.title.set(title)
                await ctx.send("The title heading has been reset to default.")
            else:
                await self.config.title.set(title)
                await ctx.send("The title heading has been updated.")
        except Exception as error:
            log.exception("Failed to update title setting.")
            await ctx.send(f"Failed to update title: `{error}`")

    @invite_settings.command(name="footer")
    async def invite_footer(self, ctx: commands.Context, *, footer: NoneConverter) -> None:
        """Set a small subtext footer at the bottom of the container.

        **Live Placeholders:**
        • `{bot_name}`: The bot's name
        • `{guild_count}`: Number of servers the bot is in
        • `{user_count}`: Total users served

        **Usage:**
        • `[p]invite set footer Serving {user_count} users across {guild_count} servers.`
        • `[p]invite set footer none` (removes the footer)
        """
        try:
            if not footer:
                await self.config.footer.set(None)
                await ctx.send("The footer has been removed.")
                return
            if len(footer) > 100:
                await ctx.send("The footer cannot exceed 100 characters in length.")
                return
            await self.config.footer.set(footer)
            await ctx.send("The footer has been updated.")
        except Exception as error:
            log.exception("Failed to update footer setting.")
            await ctx.send(f"Failed to update footer: `{error}`")

    @invite_settings.command(name="color", aliases=("colour", "accent"))
    async def invite_color(self, ctx: commands.Context, *, color: ColorNoneConverter) -> None:
        """Set the border/accent color of the container.

        **Usage:**
        • Hex code: `[p]invite set color #5865F2`
        • Color name: `[p]invite set color blurple` or `[p]invite set color dark_teal`
        • Reset: `[p]invite set color default`
        """
        try:
            if color is None:
                color = _config_structure["accent_color"]
                await self.config.accent_color.set(color)
                await ctx.send(f"The accent color has been reset to default Blurple (`#{color:06X}`).")
            else:
                await self.config.accent_color.set(color)
                await ctx.send(f"The accent color has been set to `#{color:06X}`.")
        except Exception as error:
            log.exception("Failed to update accent color setting.")
            await ctx.send(f"Failed to update accent color: `{error}`")

    @invite_settings.command(name="thumbnail", aliases=("thumb", "icon"))
    async def invite_thumbnail(self, ctx: commands.Context, *, thumbnail: ThumbnailConverter) -> None:
        """Set a compact thumbnail image next to the title and message.

        **Usage:**
        • Use bot avatar: `[p]invite set thumbnail bot`
        • Direct image link: `[p]invite set thumbnail https://example.com/logo.png`
        • Remove thumbnail: `[p]invite set thumbnail none`
        """
        try:
            if thumbnail is None:
                await self.config.thumbnail.set(None)
                await ctx.send("The thumbnail has been removed.")
            elif thumbnail == "bot":
                await self.config.thumbnail.set("bot")
                await ctx.send("The thumbnail has been configured to display the bot's profile avatar.")
            else:
                await self.config.thumbnail.set(thumbnail)
                await ctx.send(f"The thumbnail has been set to: <{thumbnail}>")
        except Exception as error:
            log.exception("Failed to update thumbnail setting.")
            await ctx.send(f"Failed to update thumbnail: `{error}`")

    @invite_settings.command(name="showsettings")
    async def invite_show_settings(self, ctx: commands.Context) -> None:
        """Display an overview of all active settings."""
        try:
            settings = await self.config.all()
            color_val = settings.get("accent_color", 5793266)
            hex_color = f"#{color_val:06X}" if color_val is not None else "None"
            thumb_display = "Bot Avatar" if settings.get("thumbnail") == "bot" else (settings.get("thumbnail") or "None")
            custom_invite = settings.get("custom_invite")
            invite_display = f"<{custom_invite}> (Custom)" if custom_invite else "Default Bot Invite URL (Dynamic)"

            lines = [
                f"• **Title:** {settings.get('title')}",
                f"• **Custom Message:** {settings.get('custom_message')}",
                f"• **Invite URL:** {invite_display}",
                f"• **Support Server:** {settings.get('support_server') or 'None (Button Hidden)'}",
                f"• **Footer:** {settings.get('footer') or 'None'}",
                f"• **Accent Color:** {hex_color} (`{color_val}`)",
                f"• **Thumbnail:** {thumb_display}",
            ]
            msg = "**Advanced Invite V2 Settings Overview**\n\n" + "\n".join(lines)
            await ctx.send(msg)
        except Exception as error:
            log.exception("Failed to display settings.")
            await ctx.send(f"Failed to display settings: `{error}`")
