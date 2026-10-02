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
                sources = [self._get_randomfox, self._get_reddit_fox]
                source_func = random.choice(sources)
                image_url, source = await source_func()

                if not image_url:
                    other_source = [s for s in sources if s != source_func][0]
                    image_url, source = await other_source()

                if not image_url:
                    return await ctx.send("❌ Could not find a fox right now. Try again later!")

                embed = discord.Embed(
                    title="🦊 Random Fox",
                    color=discord.Color.orange()
                )
                embed.set_image(url=image_url)
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name} | Source: {source}",
                    icon_url=ctx.author.display_avatar.url
                )

                await ctx.send(embed=embed)

            except aiohttp.ClientError:
                await ctx.send("❌ The fox service is currently unavailable.")
            except Exception:
                await ctx.send("❌ An unexpected error occurred while fetching a fox.")

    async def _get_randomfox(self):
        """Fetch from randomfox.ca"""
        api_url = "https://randomfox.ca/floof/"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        image_url = data.get("image")
                        if image_url:
                            return image_url, "randomfox.ca"
        except Exception:
            pass
        return None, None

    async def _get_reddit_fox(self):
        """Fetch from r/foxes"""
        subreddits = ["foxes", "Foxes", "IllegallySmolFoxes"]
        subreddit = random.choice(subreddits)
        api_url = f"https://www.reddit.com/r/{subreddit}/top.json?sort=top&t=week&limit=100"

        try:
            headers = {
                "User-Agent": "/r/foxes_discord_bot"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        return None, None

                    data = await response.json()
                    posts = data.get("data", {}).get("children", [])

                    if not posts:
                        return None, None

                    random.shuffle(posts)

                    for item in posts:
                        try:
                            post = item.get("data", {})
                            url = post.get("url", "")

                            if url.endswith((".jpg", ".jpeg", ".png", ".gif")):
                                return url, "Reddit"

                            if "i.redd.it" in url or "i.imgur.com" in url:
                                return url, "Reddit"
                        except Exception:
                            continue

        except Exception:
            pass

        return None, None