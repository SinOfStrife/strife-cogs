from redbot.core.bot import Red
from .fox import Fox


async def setup(bot: Red) -> None:
    await bot.add_cog(Fox(bot))