# Fox

A fun Red-DiscordBot cog that fetches random cute fox pictures paired with interesting facts.

---

## Key Features

* **Parallel Fetching:** Retrieves images from `randomfox.ca` and facts from `some-random-api.com` simultaneously with zero added lag.
* **Graceful Fallback:** If the fact API goes offline, the bot still posts the fox picture normally without breaking.
* **Permission Safe:** Falls back to plain text if the bot lacks permission to post embeds in a channel.
* **Rate Limited:** Protected by a user-level cooldown to prevent API abuse.

---

## Installation

    [p]cog install strife-cogs fox
    [p]load fox

---

## Commands

* `[p]fox` *(alias: `[p]foxo`)* — Display a random cute fox picture with a fun fact.