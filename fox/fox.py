import aiohttp
import discord
from redbot.core import commands
from redbot.core.bot import Red


class Fox(commands.Cog):
    """Brings random cute foxes straight to your chat."""

    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command(name="fox", aliases=["foxo"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def fox(self, ctx: commands.Context):
        """Get a random cute fox image or GIF!"""

        async with ctx.typing():
            try:
                image_url = await self._get_fox()

                if not image_url:
                    return await ctx.send("❌ Could not find a fox right now. Try again later!")

                embed = discord.Embed(
                    title="🦊 Random Fox",
                    color=discord.Color.orange()
                )
                embed.set_image(url=image_url)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url
                )

                await ctx.send(embed=embed)

            except aiohttp.ClientError:
                await ctx.send("❌ The fox service is currently unavailable.")
            except Exception:
                await ctx.send("❌ An unexpected error occurred while fetching a fox.")

    async def _get_fox(self):
        """Fetch from randomfox.ca"""
        api_url = "https://randomfox.ca/floof/"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("image")
        except Exception:
            pass
        return None