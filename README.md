# strife-cogs

A collection of custom cogs for Red-DiscordBot.

## Installation

To install these cogs, make sure you have the Downloader cog loaded, then run the following commands in your bot:

```ini
[p]repo add strife-cogs https://github.com/SinOfStrife/strife-cogs
```

Once the repository is added, you can install individual cogs using:
```ini
[p]cog install strife-cogs <cog_name>
```

## Available Cogs

| Cog | Description | Key Commands |
| :--- | :--- | :--- |
| **advancedinviteV2** | Sends interactive invite cards using Discord's modern Components V2 layouts, custom buttons, and live server stats. | `[p]invite`<br>`[p]invite set`<br>`/invite` |
| **Fox** | Fetches and posts random fox images or GIFs in Discord as clean embeds. | `[p]fox` |
| **NoPings** | Prevents bot reply messages from pinging users. Can be toggled server-wide or scoped to specific users. | `[p]nopings toggle`<br>`[p]nopings add @user`<br>`[p]nopings remove @user`<br>`[p]nopings test [user]` |
| **PKLens** | A privacy-focused PluralKit accessibility tool supporting ephemeral profile and fronter lookups across slash commands, DMs, and right-click context menus. | `[p]pklens`<br>`[p]pkfronters`<br>`[p]pkprofile`<br>*(Context Menus: `fronters`, `profile`)* |

## Support

If you encounter any bugs, have feature requests, or need help with any of these cogs, please open an [Issue](https://github.com/SinOfStrife/strife-cogs/issues).

## Contributors

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

## Acknowledgments

* **advancedinviteV2** is adapted from the original `advancedinvite` cog by [Jojo#7791](https://github.com/Just-Jojo/JojoCogs).

## License

This project is licensed under the [MIT License](LICENSE).
