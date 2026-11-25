# PKLens

A lightweight, privacy-focused PluralKit inspector for Discord. 

PKLens allows you to look up public PluralKit system profiles and current fronters completely silently. All lookups are ephemeral (only you can see them), preventing chat spam.

---

## Key Features

* **1-Click View Switching:** Easily toggle back and forth between a system's current fronters and their full profile using buttons.
* **Pronouns:** Shows fronters with their pronouns for better accessibility.
* **Dual Installation (Server & User App):** 
  * Add it to a server so every member can use it automatically.
  * Install it as a personal User App on your Discord account to use it privately across DMs, group chats, and external servers.
* **Right-Click Integration:** Quickly inspect any user via profile context menus (`Apps ➔ Fronter` or `Profile`).

---

## Installation

    [p]cog install strife-cogs pklens
    [p]load pklens
    [p]slash sync

### Setting Up User Apps (Bot Owners)

To allow PKLens to be installed to personal Discord accounts for use in DMs, group chats, and external servers (**requires Red 3.5.10+ / `discord.py 2.4+`**):

1. Open the [Discord Developer Portal](https://discord.com/developers/applications) and select your bot's application.
2. Go to **Installation** in the left sidebar.
3. Under **Installation Contexts**, enable both **Guild Install** and **User Install**.
4. Set **Install Link** to **Discord Provided Link**.
5. Under **Default Install Settings**:
   * **Guild Install:** Add scopes `bot` and `applications.commands`.
   * **User Install:** Add scope `applications.commands` *(this is required for the **Add PKLens** button in `/pklens` to work)*.
6. Save changes, then run `[p]slash sync` **globally** in Red (do **not** pass a server ID—User Apps only work on global syncs) and refresh Discord (`Ctrl+R` / `Cmd+R`).

> **Notes:**
> * PKLens auto-enables its slash commands on load, so `[p]slash enablecog` is not required.
> * On Red versions older than `3.5.10`, PKLens falls back to standard server-only commands.
> * External servers that disable Discord's **Use External Apps** permission will block user-installed commands in those channels.

### Installing as a Personal User App (Users)

Once configured by the bot owner:
1. Run `/pklens` and click **Add PKLens** (or open the bot's **Discord Provided Link**).
2. Choose **Add to My Apps** to add it to your personal Discord account.

---

## Usage & Commands

* **Slash Commands:**
  * `/pklens [public]` — View info about the app and sharing options.
  * `/pkfronters <user>` — Check who is currently fronting in a system.
  * `/pkprofile <user>` — View a system's full profile, description, and pronouns.
* **Profile Context Menus (Desktop & Mobile):**
  * Right-click (or tap) a user's profile ➔ `Apps` ➔ `Fronter` or `Profile`.

---

## Privacy & Data

PKLens does not store any user data. Looking up a user sends their Discord user ID to the public PluralKit API (`api.pluralkit.me`).
