# strife-cogs

[![Red-DiscordBot](https://img.shields.io/badge/Red--DiscordBot-V3-red.svg)](https://github.com/Cog-Creators/Red-DiscordBot)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A collection of custom cogs for Red-DiscordBot.

## Installation

To install these cogs, make sure you have the Downloader cog loaded, then run the following commands in your bot:

1. Add this repository to your bot:
```ini
[p]repo add strife-cogs https://github.com/SinOfStrife/strife-cogs
```

2. Install the cog you want:
```ini
[p]cog install strife-cogs <cog_name>
```

3. Load the cog:
```ini
[p]load <cog_name>
```

> **Note:** For cogs featuring application commands (`advancedinviteV2`, `PKLens`), run `[p]slash sync` if the commands do not appear immediately.

---

## Available Cogs

| Cog | Description | Key Commands |
| :--- | :--- | :--- |
| **advancedinviteV2** | Sends interactive invite cards using Discord's modern Components V2 layouts, custom buttons, and live server stats. | `[p]invite`, `/invite`<br>`[p]invite set [url\|support\|message\|title\|footer\|color\|thumbnail\|showsettings]` |
| **Fox** | Fetches and posts random fox images or GIFs from randomfox.ca with plaintext permission fallbacks. | `[p]fox` *(alias: `[p]foxo`)* |
| **NoPings** | Prevents notification pings when the bot replies to commands. Includes personal opt-in toggles and server-wide admin controls. | `[p]noping`, `[p]nopings test [member]`<br>`[p]nopings set [toggle\|add\|remove\|showsettings]` |
| **PKLens** | A privacy-focused PluralKit accessibility tool supporting ephemeral profile and fronter lookups across slash commands and right-click context menus. | `/pklens`, `/pkfronters <user>`, `/pkprofile <user>`<br>Apps (Context Menus): `fronters`, `profile` |

---

## Data Privacy & GDPR

In accordance with Red-DiscordBot standards, all cogs declare their data retention policies:

| Cog | Stores User Data? | Purpose |
| :--- | :---: | :--- |
| **advancedinviteV2** | ❌ No | Does not store user data. |
| **Fox** | ❌ No | Does not store user data. |
| **NoPings** | ⚠️ Yes | Stores User IDs solely for personal opt-in and server-specific no-ping lists. Supports `[p]mydata` deletion. |
| **PKLens** | ❌ No | Ephemeral PluralKit API lookups only; no data is persistently stored. |

---

## Support

If you encounter any bugs, have feature requests, or need help with any of these cogs, please open an [Issue](https://github.com/SinOfStrife/strife-cogs/issues).

---

## Contributors

Contributions are welcome! Before opening a pull request, please make sure your changes follow standard Red-DiscordBot cog guidelines, pass linting checks, and include any relevant End-User Data statement updates.

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center" valign="top" width="14.28%"><a href="https://github.com/Xanderxx46"><img src="https://github.com/Xanderxx46.png?size=100" width="100px;" alt="Xanderxx46"/><br /><sub><b>Xanderxx46</b></sub></a><br /><a href="https://github.com/SinOfStrife/strife-cogs/commits?author=Xanderxx46" title="Code">💻</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->
[![All Contributors](https://img.shields.io/github/all-contributors/SinOfStrife/strife-cogs?color=ee8449&style=flat-square)](#contributors)

---

## Acknowledgments

* **advancedinviteV2** is adapted from the original `advancedinvite` cog by [Jojo#7791](https://github.com/Just-Jojo/JojoCogs).

---

## License

This project is licensed under the [MIT License](LICENSE).
