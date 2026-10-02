import aiohttp
import discord
import random
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

        sources = [
            self._get_randomfox,
            self._get_reddit_fox,
        ]

        async with ctx.typing():
            try:
                source = random.choice(sources)
                image_url = await source()

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

    async def _get_randomfox(self) -> str:
        """Fetch from randomfox.ca"""
        api_url = "https://randomfox.ca/floof/"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("image")
        except Exception:
            return None

    async def _get_reddit_fox(self) -> str:
        """Fetch from a fox-specific subreddit"""
        subreddits = ["foxes", "Foxes", "IllegallySmolFoxes"]
        subreddit = random.choice(subreddits)
        api_url = f"https://www.reddit.com/r/{subreddit}/random.json"

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data or not data[0].get("data", {}).get("children"):
                            return None
                        post = data[0]["data"]["children"][0]["data"]
                        url = post.get("url")
                        if url and url.endswith((".jpg", ".jpeg", ".png", ".gif", ".gifv")):
                            return url
        except Exception:
            return None