import asyncio
import logging
from typing import Optional, Tuple

import aiohttp
import discord
from redbot.core import commands
from redbot.core.bot import Red

log = logging.getLogger("red.fox")


class Fox(commands.Cog):
    """Brings random cute foxes straight to your chat."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.session: Optional[aiohttp.ClientSession] = None

    async def cog_load(self) -> None:
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"User-Agent": "strife-cogs/fox (https://github.com/SinOfStrife/strife-cogs)"},
        )

    async def cog_unload(self) -> None:
        if self.session is not None and not self.session.closed:
            await self.session.close()
        self.session = None

    @commands.command(name="fox", aliases=["foxo"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def fox(self, ctx: commands.Context):
        """Get a random cute fox image or GIF!"""

        async with ctx.typing():
            try:
                image_url, failed = await self._get_fox()
            except Exception:
                log.exception("Unexpected error while fetching a fox.")
                await ctx.send("❌ An unexpected error occurred while fetching a fox.")
                return

            if failed:
                await ctx.send("❌ The fox service is currently unavailable.")
                return
            if not image_url:
                await ctx.send("❌ Could not find a fox right now. Try again later!")
                return

            embed = discord.Embed(title="🦊 Random Fox", color=discord.Color.orange())
            embed.set_image(url=image_url)
            embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url,
            )
            await ctx.send(embed=embed)

    async def _get_fox(self) -> Tuple[Optional[str], bool]:
        """Return (image URL, failed). failed is True when the request itself did not succeed."""
        if self.session is None or self.session.closed:
            return None, True

        try:
            async with self.session.get("https://randomfox.ca/floof/") as response:
                if response.status != 200:
                    return None, True
                data = await response.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            return None, True

        if not isinstance(data, dict):
            return None, True
        image = data.get("image")
        if not isinstance(image, str) or not image:
            return None, False
        return image, False
