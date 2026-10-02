from .fox import fox

async def setup(bot):
    await bot.add_cog(Fox(bot))
  
