# Copyright (c) 2026 Jojo#7791, sinofstrife and Contributors
# Licensed under the MIT License

import logging
from typing import Optional, Union
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
    ) -> Union[discord.Invite, str, None]:
        if argument.lower() in ("none", "nil", "null", "reset"):
            return None
        try:
            invite = await discord.Invite.from_url(ctx.bot, argument)
            return invite
        except discord.NotFound:
            raise commands.BadArgument("That invite link is invalid or has expired.")
        except discord.HTTPException:
            raise commands.BadArgument("Discord encountered an error while verifying that invite link.")


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
