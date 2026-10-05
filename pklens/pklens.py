import aiohttp
import discord
from redbot.core import app_commands, commands


class PKLens(commands.Cog):
    """A privacy-focused PluralKit inspector for Discord Context Menus and Slash Commands."""

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.headers = {
            "User-Agent": "PKLens/1.0 (https://github.com/SinOfStrife)"
        }

        # Create context menus explicitly with clean standard names
        self.check_fronters_menu = app_commands.ContextMenu(
            name="fronters",
            callback=self.check_fronter_callback
        )
        self.view_profile_menu = app_commands.ContextMenu(
            name="profile",
            callback=self.view_profile_callback
        )

        bot.tree.add_command(self.check_fronters_menu)
        bot.tree.add_command(self.view_profile_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.check_fronters_menu.name, type=self.check_fronters_menu.type)
        self.bot.tree.remove_command(self.view_profile_menu.name, type=self.view_profile_menu.type)

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
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(public="Set to True to share the info message with the channel (default: False)")
    async def pklens_help(self, interaction: discord.Interaction, public: bool = False):
        embed = discord.Embed(
            title="🔍 PKLens",
            description="A lightweight, privacy-focused tool designed to make viewing public PluralKit system profiles and current fronters accessible across Discord."
        )
        embed.add_field(
            name="How to use",
            value="Use slash commands or right-click any user via their profile (`Apps` ➔ `fronters` or `profile`).",
            inline=False
        )
        embed.add_field(
            name="Privacy",
            value="Lookups are ephemeral (only you see them) to respect PluralKit privacy settings. `/pklens` can be made public to introduce the app to others.",
            inline=False
        )
        embed.set_footer(text="Inspired by the Gayos of chaos")
        await interaction.response.send_message(embed=embed, ephemeral=not public)

    @app_commands.command(
        name="pkfronters",
        description="Check who is currently fronting in a user's PluralKit system."
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
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
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
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

    async def check_fronter_callback(self, interaction: discord.Interaction, user: discord.User):
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

    async def view_profile_callback(self, interaction: discord.Interaction, user: discord.User):
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
