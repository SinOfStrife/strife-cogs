# Copyright (c) 2021-2026 Jojo#7791, SinOfStrife and Contributors
# Licensed under the MIT License

from redbot.core.bot import Red
from .advanced_invite_v2 import AdvancedInviteV2


async def setup(bot: Red) -> None:
    await bot.add_cog(AdvancedInviteV2(bot))