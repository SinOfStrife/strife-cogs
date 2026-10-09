from redbot.core.bot import Red
from .nopings import NoPings

async def setup(bot: Red) -> None:
    await bot.add_cog(NoPings(bot))