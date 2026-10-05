from .pklens import PKLens

async def setup(bot):
    await bot.add_cog(PKLens(bot))
