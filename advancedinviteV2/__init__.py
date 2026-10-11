# Copyright (c) 2021-2026 Jojo#7791, SinOfStrife and Contributors
# Licensed under MIT

from redbot.core.bot import Red
from redbot.core.utils import get_end_user_data_statement
from .advanced_invite_v2 import AdvancedInviteV2

__red_end_user_data_statement__ = get_end_user_data_statement(__file__)


async def setup(bot: Red) -> None:
    await bot.add_cog(AdvancedInviteV2(bot))
