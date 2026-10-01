import discord
from redbot.core import commands, Config

class NoPings(commands.Cog):
    """Suppresses bot reply pings globally or for designated users."""

    def __init__(self, bot):
        self.bot = bot
        # Unique 10-digit ID for data storage
        self.config = Config.get_conf(self, identifier=8473920194, force_registration=True)
        
        default_guild = {
            "enabled": False,
            "blocked_users": []
        }
        self.config.register_guild(**default_guild)

    @commands.Cog.listener()
    async def on_message_before_sending(self, message: discord.Message):
        """Hook into outgoing messages to disable reply pings when conditions are met."""
        if not message.guild or not message.reference:
            return

        enabled = await self.config.guild(message.guild).enabled()
        blocked_users = await self.config.guild(message.guild).blocked_users()

        target_user_id = message.reference.cached_message.author.id if message.reference.cached_message else None

        if enabled or (target_user_id and target_user_id in blocked_users):
            allowed = message.allowed_mentions or discord.AllowedMentions()
            allowed.replied_user = False
            message.allowed_mentions = allowed

    @commands.group(name="nopings", invoke_without_command=True)
    async def nopings(self, ctx: commands.Context):
        """Manage no-ping bot reply settings."""
        await ctx.send_help(ctx.command)

    @nopings.command(name="toggle")
    async def toggle(self, ctx: commands.Context):
        """Toggle ping-less bot replies on or off for the server."""
        current = await self.config.guild(ctx.guild).enabled()
        new_state = not current
        await self.config.guild(ctx.guild).enabled.set(new_state)

        emoji = "✅" if new_state else "❌"
        
        try:
            await ctx.message.add_reaction(emoji)
        except discord.HTTPException:
            pass

        if new_state:
            text = "✅ Got it! Bot reply pings are turned off for the whole server now."
        else:
            text = "❌ Bot reply pings are back on for the server."

        await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())

    @nopings.command(name="add")
    async def add_user(self, ctx: commands.Context, user: discord.Member):
        """Add a specific user so the bot won't ping when replying to them."""
        async with self.config.guild(ctx.guild).blocked_users() as blocked:
            if user.id in blocked:
                await ctx.send(
                    f"✅ **{user.display_name}** is already on the no-ping list!",
                    allowed_mentions=discord.AllowedMentions.none()
                )
                return
            blocked.append(user.id)

        try:
            await ctx.message.add_reaction("✅")
        except discord.HTTPException:
            pass

        await ctx.send(
            f"✅ Added **{user.display_name}** to the list—I won't ping them when replying anymore.",
            allowed_mentions=discord.AllowedMentions.none()
        )

    @nopings.command(name="remove")
    async def remove_user(self, ctx: commands.Context, user: discord.Member):
        """Remove a specific user from the no-ping bot reply list."""
        async with self.config.guild(ctx.guild).blocked_users() as blocked:
            if user.id not in blocked:
                await ctx.send(
                    f"❌ **{user.display_name}** wasn't on the no-ping list anyway.",
                    allowed_mentions=discord.AllowedMentions.none()
                )
                return
            blocked.remove(user.id)

        try:
            await ctx.message.add_reaction("❌")
        except discord.HTTPException:
            pass

        await ctx.send(
            f"❌ Removed **{user.display_name}** from the list. Normal bot reply pings will work for them again.",
            allowed_mentions=discord.AllowedMentions.none()
        )

    @nopings.command(name="test")
    async def test_ping(self, ctx: commands.Context, target: discord.Member = None):
        """Test bot reply ping status for yourself or another user."""
        target_user = target or ctx.author
        enabled = await self.config.guild(ctx.guild).enabled()
        blocked_users = await self.config.guild(ctx.guild).blocked_users()
        is_user_blocked = target_user.id in blocked_users

        should_suppress = enabled or is_user_blocked

        if enabled:
            emoji = "✅"
            msg = f"✅ Bot reply pings are **disabled** server-wide. Bot replies to **{target_user.display_name}** will **not** ping them."
        elif is_user_blocked:
            emoji = "✅"
            msg = f"✅ **{target_user.display_name}** is on the no-ping list. Bot replies to them will **not** ping them."
        else:
            emoji = "❌"
            msg = f"❌ No-ping mode is **off** for **{target_user.display_name}**. Bot replies to them **will** ping as normal."

        try:
            await ctx.message.add_reaction(emoji)
        except discord.HTTPException:
            pass

        # Disable all text and reply mentions when ping suppression is active
        if should_suppress:
            allowed = discord.AllowedMentions.none()
        else:
            allowed = discord.AllowedMentions(users=True, replied_user=True)

        await ctx.reply(msg, allowed_mentions=allowed)
        
