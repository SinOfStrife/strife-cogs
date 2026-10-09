# Copyright (c) 2021-2026 Jojo#7791, SinOfStrife and Contributors
# Licensed under the MIT License

import logging
from typing import Optional, Union
from urllib.parse import urlparse

import discord
from redbot.core import commands

log = logging.getLogger("red.advancedinvitev2.utils")


class NoneConverter(commands.Converter):
    strict: bool = False

    async def convert(self, ctx: commands.Context, argument: str) -> Optional[str]:
        if argument.lower() in ("none", "nil", "null"):
            return None
        if self.strict and argument.lower() == "default":
            return None
        return argument


class NoneStrict(NoneConverter):
    strict: bool = True


class InviteNoneConverter(commands.Converter):
    async def convert(
        self, ctx: commands.Context, argument: str
    ) -> Optional[str]:
        if argument.lower() in ("none", "nil", "null", "reset", "clear", "disable"):
            return None

        cleaned = argument.strip().strip("<>").strip()
        if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            cleaned = f"https://{cleaned}"

        parsed = urlparse(cleaned)
        if not parsed.netloc or parsed.scheme not in ("http", "https") or len(cleaned) > 512:
            raise commands.BadArgument(
                "Please provide a valid web link starting with `http://` or `https://` (max 512 characters)."
            )

        # If it is a Discord server invite, verify it; otherwise, allow external/off-Discord links
        if any(domain in parsed.netloc for domain in ("discord.gg", "discord.com")):
            if "oauth2" not in cleaned.lower() and "authorize" not in cleaned.lower():
                try:
                    invite = await ctx.bot.fetch_invite(cleaned)
                    return invite.url
                except discord.NotFound:
                    raise commands.BadArgument("That Discord invite link is invalid or has expired.")
                except discord.HTTPException:
                    pass  # Allow through if Discord API encounters a transient verification error

        return cleaned


class ColorNoneConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> Optional[int]:
        if argument.lower() in ("none", "nil", "null", "reset", "default"):
            return None
        clean_arg = argument.lstrip("#")
        try:
            return int(clean_arg, 16)
        except ValueError:
            pass
        try:
            color = await commands.ColorConverter().convert(ctx, argument)
            return color.value
        except commands.BadArgument:
            raise commands.BadArgument(
                f"Could not convert `{argument}` to a valid color.\n"
                "**Examples:** `#5865F2`, `blurple`, `red`, `0x2ecc71`, or `default` to reset."
            )


class ThumbnailConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> Optional[str]:
        if argument.lower() in ("none", "nil", "null", "reset", "remove"):
            return None
        if argument.lower() in ("bot", "avatar", "me", "auto"):
            return "bot"
        if argument.startswith(("http://", "https://")):
            return argument
        raise commands.BadArgument(
            "Invalid thumbnail choice.\n"
            "• Use `bot` to use the bot's profile avatar.\n"
            "• Provide a direct link starting with `http://` or `https://`.\n"
            "• Use `none` to remove the thumbnail entirely."
        )