# AutoWaifuClaimer
Auto claims from Discord Mudae bot. Adapted from my previous (now obsolete) AutoWaifuClaimer project, which used a Discord bot to listen for roll events and reacted using the pyinput module and the official Discord client. The previous implementation came with the major limitation of requiring Discord to be the main focused window, preventing the user from doing any other tasks at the same time. This new implementation solves that problem and is overall significantly more reliable and consistent.

## Features
- Automatically rolling at set intervals and (optionally) only if a claim is available
- Automatically claiming `$daily` and `$dk`
- Automatically claiming waifus that are listed in `data/likelist.txt`, only if claim is available
- Automatically claiming kakera loot when available
- DM the main user on:
  - Attempted claim
  - Attempted kakera react
  - Keys rolled
- Log all rolled characters
- Can run in the background 24/7
- Cross platform support

## Limitations and bugs
- You tell me :)

## Requirements
- Firefox and [geckodriver](https://github.com/mozilla/geckodriver/releases)
- Python 3.8+ (haven't tested on 3.7)
- Python modules: see `requirements.txt`

## How it works
There are essentially three different processes running at the same time in this program. The first one opens browser Discord a headless Firefox window and attempts to login with provided credentials. The second one activates a Discord bot that will be listening for rolls and other activity. The last process controls the timers for rolling, claiming, kakera loots, and daily commands. Upon startup, the browser program will send a `$tu` command, which will be parsed by the bot. This will determine the time to next claim, roll, and daily. User commands are sent through Selenium keyboard actions to simulate a real user typing into the message box. Emoji reactions are interacted by executing Javascript on the site to click a specified reaction. As the program runs, the bot will continuously listen for rolls and parse them with regex (credit to [Znunu/EzMudae](https://github.com/Znunu/EzMudae) for the regex strings). If the roll is unclaimed and matches a name from the likelist, it automatically attempts a claim if one is available. Similarly, if a roll is already claimed, it automatically attempts a kakera loot if one is available. Lastly, if the roll is already claimed by the main user (specified in `config.py`), the bot will DM the user of a new key.

## Usage
Clone this repository and fill in the data in `config.py`. See that file for more information. For information about copying Discord IDs, see [here](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-). For information about making a bot see [here](https://www.writebots.com/discord-bot-token/).

The bot must have the following permissions:
- View Channels
- Read Message History

Add wishes to `likelist.txt`. See that file for more information.

Install Python 3.8+ and required modules. Optionally make a new virtual environment for it.

`pip install -r requirements.txt`

Install Firefox and geckodriver. This will be used for the browser Discord control. Put the path to the geckodriver executable in `config.py`. To start the bot, run `bot.py`.

Windows/Linux binaries have not been created and I don't think I will unless there is a strong demand for them.

## Credits
Regex strings for parsing the Mudae embed was adapted from Znunu's EzMudae module available at https://github.com/Znunu/EzMudae.

## License
Released under GNU GPL 3. See `LICENSE` for details.

## Disclaimer
This project was mostly designed as a proof of concept. I am not responsible for banned user accounts or salty friends. Use at your own risk.

This project also collects your Discord email and password in **plaintext**. Although it does not use this information for any purpose other than to login to Discord on the web, please keep this information safe so that it is not accidentally accessed by other users of the computer. Also, feel free to manually audit the source code to see where exactly the information is being used (the only instance is in `browsers.Browser.browser_login()`).
