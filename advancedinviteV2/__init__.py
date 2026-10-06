# Copyright (c) 2026 Jojo#7791, sinofstrife and Contributors
# Licensed under the MIT License

import json
import pathlib
from redbot.core.bot import Red
from .advanced_invite_v2 import AdvancedInviteV2

with open(pathlib.Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red) -> None:
    cog = AdvancedInviteV2(bot)
    await bot.add_cog(cog)
