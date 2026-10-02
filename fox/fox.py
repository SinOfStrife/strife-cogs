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

        async with ctx.typing():
            try:
                image_url = await self._get_randomfox()
                if not image_url:
                    image_url = await self._get_reddit_fox()

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
        """Fetch a fox post from a fox subreddit"""
        subreddits = ["foxes", "Foxes", "IllegallySmolFoxes"]
        subreddit = random.choice(subreddits)
        api_url = f"https://www.reddit.com/r/{subreddit}/top.json"

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            }
            params = {"limit": 25, "t": "week"}

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()
                    children = data.get("data", {}).get("children", [])
                    if not children:
                        return None

                    for item in children:
                        post = item.get("data", {})
                        url = post.get("url")
                        if not url:
                            continue

                        if url.endswith((".jpg", ".jpeg", ".png", ".gif", ".gifv")):
                            return url

                    # If the top posts aren't image URLs, try a second pass
                    for item in children:
                        post = item.get("data", {})
                        url = post.get("url")
                        if not url:
                            continue

                        if "i.redd.it" in url or "i.imgur.com" in url:
                            return url

        except Exception:
            return None

        return None