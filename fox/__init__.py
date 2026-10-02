from .fox import Fox

async def setup(bot):
    await bot.add_cog(Fox(bot))
  
