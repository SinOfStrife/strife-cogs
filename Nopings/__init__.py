from redbot.core.bot import Red
from .nopings import NoPings

__red_end_user_data_statement__ = (
    "This cog stores Discord User IDs on a per-guild basis to maintain a no-ping reply list."
)


async def setup(bot: Red) -> None:
    cog = NoPings(bot)
    await bot.add_cog(cog)
