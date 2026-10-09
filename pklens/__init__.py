from redbot.core.bot import Red
from .pklens import PKLens


async def setup(bot: Red) -> None:
    await bot.add_cog(PKLens(bot))