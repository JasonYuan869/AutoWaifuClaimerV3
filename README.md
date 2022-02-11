# (Updated 02/10/2020)
Major Updates Include:
- Simplified setup using docker containers
- Much more consistent $tu parsing (manually input $tu)
- Hardcoded Xpath's to prevent failures on DOM element changes
- Optimized Logic for easier debugging
- Greater control through config file
- Greater security using .env files
- Optimized waifu_list to account for duplicates
- Support through Discord! @ NerdyK#9470
- Various other changes improved stability
# AutoWaifuClaimer
Auto claims from Discord Mudae bot. Adapted from my previous (now obsolete) AutoWaifuClaimer project, which used a Discord bot to listen for roll events and reacted using the pyinput module and the official Discord client. The previous implementation came with the major limitation of requiring Discord to be the main focused window, preventing the user from doing any other tasks at the same time. This new implementation solves that problem and is overall significantly more reliable and consistent.

## Features
- Automatically rolling at set intervals and (optionally) only if a claim is available
- Automatically claiming `$daily` and `$dk`
- Automatically sending `$im`
- Automatically claiming waifus that are listed in `data/lovelist.txt`, only if claim is available
- Automatically claiming kakera loot when available
- DM the main user on:
  - Attempts to claim
  - Attempts to react to kakera
  - Keys rolled
  - Alerts for liked characters
- Log all rolled characters
- Can run in the background 24/7
- Cross-platform support (?)

## Limitations and bugs
- Some unexpected behaviour

## Requirements
- Docker Desktop | https://www.docker.com/products/docker-desktop


## How it works
There are essentially three different processes running at the same time in this program. The first one opens browser Discord a headless Firefox window and attempts to login with provided credentials. The second one activates a Discord bot that will be listening for rolls and other activity. The last process controls the timers for rolling, claiming, kakera loots, and daily commands. Upon startup, the browser program will send a `$tu` command, which will be parsed by the bot. This will determine the time to next claim, roll, and daily. User commands are sent through Selenium keyboard actions to simulate a real user typing into the message box. Emoji reactions are interacted by executing Javascript on the site to click a specified reaction. As the program runs, the bot will continuously listen for rolls and parse them with regex (credit to [Znunu/EzMudae](https://github.com/Znunu/EzMudae) for the regex strings). If the roll is unclaimed and matches a name from the likelist, it automatically attempts a claim if one is available. Similarly, if a roll is already claimed, it automatically attempts a kakera loot if one is available. Lastly, if the roll is already claimed by the main user (specified in `config.py`), the bot will DM the user of a new key.

## Using with Docker Steps

- Download & Install Docker Desktop (Windows is awful so it will likely restart then ask you to install a Linux Kernel)

- Update `example.env` file `waifu_list/lovelist.txt` and `waifu_list/lovelist.txt`.

- Change `example.env` name to `.env`

- Update `config/config.py` file. (Requires credentials, **DO NOT** Version Control with credentials loaded)

- In the terminal, build the docker image for the python folder (Dockerfile Included): `docker build --tag waifu-claimer-v3 .`

- In terminal, start firefox container: `docker run -d --name firefox -e SE_NODE_OVERRIDE_MAX_SESSIONS=true -e SE_NODE_MAX_SESSIONS=3 -e SE_NODE_SESSION_TIMEOUT=86400 -p 4446:4444 -v /dev/shm:/dev/shm selenium/standalone-firefox`

- In the terminal, run the build you created with: `docker run --name waifu-claimer waifu-claimer-v3`

If anything is not working, triple check you updated all the files above correctly, including adding every parameter to `example.env` 

If you alter any of the files after getting to the step with docker build you will have to run the `docker build --tag waifu-claimer-v3 .` again. (It's much faster)

Sometimes the bot fails to parse $tu, if it does fail just try to run it again.

Using the Docker UI to manually reset containers is ok, sometimes connections get stuck. 

Try your best to troubleshoot before submitting an issue :).

## Credits
Regex strings for parsing the Mudae embed was adapted from Znunu's EzMudae module available at https://github.com/Znunu/EzMudae.

## License
Released under MIT. See `LICENSE` for details.

## Disclaimer
This project was mostly designed as a proof of concept. I am not responsible for banned user accounts or salty friends. Use at your own risk.

This project also collects your Discord email and password in **plaintext**. Although it does not use this information for any purpose other than to login to Discord on the web, please keep this information safe so that it is not accidentally accessed by other users of the computer. Also, feel free to manually audit the source code to see where exactly the information is being used (the only instance is in `browsers.Browser.browser_login()`).
