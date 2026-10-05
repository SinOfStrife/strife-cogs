import aiohttp
import discord
from redbot.core import app_commands, commands


class PKLens(commands.Cog):
    """A privacy-focused PluralKit inspector for Discord Context Menus and Slash Commands."""

    def __init__(self, bot):
        self.bot = bot
        self.headers = {
            "User-Agent": "PKLens/1.0 (https://github.com/SinOfStrife)"
        }

    async def fetch_pk_data(self, endpoint: str):
        """Fetches PluralKit data from the official API."""
        url = f"https://api.pluralkit.me/v2{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status == 404:
                    return {"error": "not_found"}
                if resp.status == 403:
                    return {"error": "private"}
                if resp.status == 429:
                    return {"error": "rate_limited"}
                if resp.status != 200:
                    return {"error": "api_error"}
                return await resp.json()

    async def _send_pk_error(self, interaction: discord.Interaction, user: discord.User, error: str, kind: str):
        """Send a consistent user-only error message for the selected PK check."""
        if error == "not_found":
            msg = f"**{user.name}** is either not registered with PluralKit or does not have a public profile."
        elif error == "private":
            if kind == "system":
                msg = f"**{user.name}** has set their system profile to **private**."
            else:
                msg = f"**{user.name}** has set their fronter information to **private**."
        elif error == "rate_limited":
            msg = "PluralKit is rate-limiting requests right now. Please try again in a moment."
        else:
            msg = "An error occurred while communicating with the PluralKit API."

        embed = discord.Embed(
            title="⚠️ Error",
            description=msg,
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="pklens",
        description="View info about the PKLens app and how to use it."
    )
    async def pklens_help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔍 PKLens - PluralKit Inspector",
            description="A lightweight, privacy-focused tool to inspect public PluralKit system profiles and current fronters directly from Discord."
        )
        embed.add_field(
            name="How to use",
            value="Use the `/pklens` command or right-click any user, go to **Apps**, and select **PK: Check Fronters** or **PK: View Profile**.",
            inline=False
        )
        embed.add_field(
            name="Privacy",
            value="All responses are visible only to you (`ephemeral`). This respects PluralKit privacy settings.",
            inline=False
        )
        embed.set_footer(text="Built for the mythos-cogs collection.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="pkfronters",
        description="Check who is currently fronting in a user's PluralKit system."
    )
    async def pkfronters_slash(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=True)
        data = await self.fetch_pk_data(f"/systems/{user.id}/fronters")

        if "error" in data:
            await self._send_pk_error(interaction, user, data["error"], "fronters")
            return

        fronters = data.get("members", [])
        if not fronters:
            empty_embed = discord.Embed(
                title=f"🟢 Current Fronters: {user.name}",
                description="No system members are currently fronting.",
                color=discord.Color.dark_grey()
            )
            await interaction.followup.send(embed=empty_embed, ephemeral=True)
            return

        names = [member.get("name") or "Unknown" for member in fronters if member.get("name")]
        description = ", ".join(names) if names else "Unknown"

        fronter_embed = discord.Embed(
            title=f"🟢 Current Fronters: {user.name}",
            description=description,
            color=discord.Color.green()
        )

        first_member = fronters[0] if fronters else {}
        avatar_url = first_member.get("avatar_url")
        if avatar_url:
            fronter_embed.set_thumbnail(url=avatar_url)

        await interaction.followup.send(embed=fronter_embed, ephemeral=True)

    @app_commands.command(
        name="pkprofile",
        description="View a user's PluralKit system profile."
    )
    async def pkprofile_slash(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=True)
        data = await self.fetch_pk_data(f"/systems/{user.id}")

        if "error" in data:
            await self._send_pk_error(interaction, user, data["error"], "system")
            return

        system_name = data.get("name") or user.name
        tag = data.get("tag")
        system_title = f"{system_name} [{tag}]" if tag else system_name

        description = data.get("description") or "No description provided."
        pronouns = data.get("pronouns") or "Not specified."

        color_hex = data.get("color")
        embed_color = discord.Color.default()
        if color_hex:
            try:
                embed_color = discord.Color(int(color_hex, 16))
            except ValueError:
                pass

        embed = discord.Embed(
            title=system_title,
            description=description,
            color=embed_color
        )
        embed.add_field(name="Pronouns", value=pronouns, inline=True)

        if data.get("avatar_url"):
            embed.set_thumbnail(url=data["avatar_url"])

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.context_menu(name="PK: Check Fronters")
    async def check_fronter(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=True)
        data = await self.fetch_pk_data(f"/systems/{user.id}/fronters")

        if "error" in data:
            await self._send_pk_error(interaction, user, data["error"], "fronters")
            return

        fronters = data.get("members", [])
        if not fronters:
            empty_embed = discord.Embed(
                title=f"🟢 Current Fronters: {user.name}",
                description="No system members are currently fronting.",
                color=discord.Color.dark_grey()
            )
            await interaction.followup.send(embed=empty_embed, ephemeral=True)
            return

        names = [member.get("name") or "Unknown" for member in fronters if member.get("name")]
        description = ", ".join(names) if names else "Unknown"

        fronter_embed = discord.Embed(
            title=f"🟢 Current Fronters: {user.name}",
            description=description,
            color=discord.Color.green()
        )

        first_member = fronters[0] if fronters else {}
        avatar_url = first_member.get("avatar_url")
        if avatar_url:
            fronter_embed.set_thumbnail(url=avatar_url)

        await interaction.followup.send(embed=fronter_embed, ephemeral=True)

    @app_commands.context_menu(name="PK: View Profile")
    async def view_profile(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=True)
        data = await self.fetch_pk_data(f"/systems/{user.id}")

        if "error" in data:
            await self._send_pk_error(interaction, user, data["error"], "system")
            return

        system_name = data.get("name") or user.name
        tag = data.get("tag")
        system_title = f"{system_name} [{tag}]" if tag else system_name

        description = data.get("description") or "No description provided."
        pronouns = data.get("pronouns") or "Not specified."

        color_hex = data.get("color")
        embed_color = discord.Color.default()
        if color_hex:
            try:
                embed_color = discord.Color(int(color_hex, 16))
            except ValueError:
                pass

        embed = discord.Embed(
            title=system_title,
            description=description,
            color=embed_color
        )
        embed.add_field(name="Pronouns", value=pronouns, inline=True)

        if data.get("avatar_url"):
            embed.set_thumbnail(url=data["avatar_url"])

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(PKLens(bot))