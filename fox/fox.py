import aiohttp
import discord
from redbot.core import commands
from redbot.core.bot import Red

class Fox(commands.Cog):
    """Brings random cute foxes straight to your chat."""

    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command(name="fox")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def fox(self, ctx: commands.Context):
        """Get a random cute fox image!"""
        api_url = "https://randomfox.ca/floof/"

        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url) as response:
                        if response.status != 200:
                            return await ctx.send("❌ Could not reach the fox API right now. Try again later!")
                        
                        data = await response.json()
                        image_url = data.get("image")

                        if not image_url:
                            return await ctx.send("❌ Received invalid data from the fox service.")

                        embed = discord.Embed(
                            title="🦊 Random Fox",
                            color=discord.Color.random()
                        )
                        embed.set_image(url=image_url)
                        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

                        await ctx.send(embed=embed)

            except Exception as e:
                await ctx.send("❌ An unexpected error occurred while fetching a fox.")
