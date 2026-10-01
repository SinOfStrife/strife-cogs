from .nopings import NoPings

async def setup(bot):
    await bot.add_cog(NoPings(bot))
  
