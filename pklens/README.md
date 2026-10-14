# PKLens

A lightweight, privacy-focused PluralKit inspector for Discord. 

PKLens allows you to look up public PluralKit system profiles and current fronters completely silently. All lookups are ephemeral (only you can see them), preventing chat spam.

---

## Key Features

* **1-Click View Switching:** Easily toggle back and forth between a system's current fronters and their full profile using interactive buttons.
* **Inline Pronouns:** Automatically formats co-fronters with their pronouns inline for better accessibility.
* **Dual Installation (Server & User App):** 
  * Add it to a server so every member can use it automatically.
  * Install it as a personal User App on your Discord account to use it privately across DMs, group chats, and external servers.
* **Right-Click Integration:** Quickly inspect any user via profile context menus (`Apps ➔ Fronter` or `Profile`).

---

## Installation

    [p]cog install strife-cogs pklens
    [p]load pklens
    [p]slash sync

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