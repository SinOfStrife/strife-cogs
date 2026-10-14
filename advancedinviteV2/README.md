# AdvancedInviteV2

A sleek, modern invite command for Red-DiscordBot using Discord's Components V2.

---

## Installation

    [p]cog install strife-cogs advancedinvitev2
    [p]load advancedinvitev2
    [p]slash sync

> **Note:** If the `/invite` slash command doesn't show up right away, make sure to run `[p]slash sync` in your bot.

---

## Features

* **V2 embedss:** Upgrades your standard bot invite into a gorgeous, modern embed with custom accent colors and thumbnail support.
* **Live Stats:** Shows your bot's current server and user count right on the card so people can see your reach.
* **Fully Customizable:** Easily change the title, message, footer, and buttons to match your bot's brand.
* **Smart DM Delivery:** Sends the invite card straight to the user's DMs so it doesn't clutter public chat channels.

---

## Commands

### User Commands
* `[p]invite` or `/invite` — Get the bot's invite card (sent to DMs).

### Owner Settings (`[p]invite set`)
* `[p]invite set url <link>` — Set a custom invite link for the main button (will default to your standard one otherwise).
* `[p]invite set support <link>` — Add a support server or website button.
* `[p]invite set message <text>` — Customize the body text (supports `{bot_name}`, `{guild_count}`, `{user_count}`).
* `[p]invite set title <text>` — Change the embed title.
* `[p]invite set footer <text>` — Add a custom footer.
* `[p]invite set color <color>` — Set the embed border/accent color.
* `[p]invite set thumbnail <choice>` — Add a image link or use the bot's avatar with `bot`.
* `[p]invite set showsettings` — View your current configuration.