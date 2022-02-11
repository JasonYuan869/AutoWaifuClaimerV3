#    AutoWaifuClaimer
#    Copyright (C) 2020 RandomBananazz
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from asyncio import TimeoutError
import discord
import sys
import re
from concurrent.futures import ThreadPoolExecutor
import threading
import logging
import datetime
import aiohttp
from config import config
from classes.browsers import Browser
from classes.timers import Timer

# noinspection PyArgumentList
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(config.LOG_FILE, 'a', 'utf-8'),
        logging.StreamHandler(sys.stdout)
    ])

# Initialize Selenium browser integration in separate module
browser = Browser()

# Declare global timer module
timer: Timer

# Main thread and Discord bot integration here
client = discord.Client()
main_user: discord.User
dm_channel: discord.DMChannel
roll_channel: discord.TextChannel
mudae: discord.Member
ready = False

# To be parsed by $tu and used for the auto roller
timing_info = {
    'claim_reset': None,
    'claim_available': None,
    'rolls_reset': None,
    'kakera_available': None,
    'kakera_reset': None,
    'daily_reset': None
}


async def add_emoji(message_id):
    await client


async def go_offline():
    await client.change_presence(status=discord.Status.offline)


async def close_bot():
    await client.close()
    client.loop.stop()
    client.loop.close()
    sys.exit()


@client.event
async def on_ready():
    await go_offline()
    # Ensure the browser is ready before proceeding (blocking call)
    try:
        browser_login.result()
    except TimeoutError or ValueError:
        await close_bot()

    def parse_tu(message):
        global timing_info
        if message.channel != roll_channel or message.author != mudae:
            return
        match = re.search(r"""^.*?(\w+).*?                                  # Group 1: Username
                                (can't|can).*?                              # Group 2: Claim available
                                (\d+(?:h\ \d+)?)(?=\*\*\ min).*?            # Group 3: Claim reset
                                (\d+(?:h\ \d+)?)(?=\*\*\ min).*?            # Group 4: Rolls reset
                                (?<=\$daily).*?(available|\d+h\ \d+).*?     # Group 5: $daily reset
                                (can't|can).*?(?=react).*?                  # Group 6: Kakera available
                                (?:(\d+(?:h\ \d+)?)(?=\*\*\ min)|(now)).*?  # Group 7: Kakera reset
                                (?<=\$dk).*?(ready|\d+h\ \d+)               # Group 8: $dk reset
                                .*$                                         # End of string
                                """, message.content, re.DOTALL | re.VERBOSE)
        if not match:
            return
        if match.group(1) != main_user.name: return
        # Convert __h __ to minutes
        times = []
        for x in [match.group(3), match.group(4), match.group(5), match.group(7)]:
            # Specifically, group 7 may be None if kakera is ready
            if x is None:
                x = 0
            elif 'h' in x:
                x = x.split('h')
                x = int(x[0]) * 60 + int(x[1])
            elif x == 'ready' or x == 'now' or x == 'available':
                x = 0
            else:
                x = int(x)
            times.append(x)
        kakera_available = match.group(6) == 'can'
        claim_available = match.group(2) == 'can'
        timing_info = {
            'claim_reset': datetime.datetime.now() + datetime.timedelta(minutes=times[0]),
            'claim_available': claim_available,
            'rolls_reset': datetime.datetime.now() + datetime.timedelta(minutes=times[1]),
            'kakera_available': kakera_available,
            'kakera_reset': datetime.datetime.now() + datetime.timedelta(minutes=times[3]),
            'daily_reset': datetime.datetime.now() + datetime.timedelta(minutes=times[2]),
        }
        return True

    global main_user, mudae, dm_channel, roll_channel, timer, timing_info, ready
    logging.info(f'Bot connected as {client.user.name} with ID {client.user.id}')
    main_user = await client.fetch_user(config.USER_ID)
    dm_channel = await main_user.create_dm()
    roll_channel = await client.fetch_channel(config.CHANNEL_ID)
    mudae = await client.fetch_user(config.MUDAE_ID)

    # Parse timers by sending $tu command
    # Only do so once by checking ready property
    if not ready:
        logging.info('Attempting to parse $tu command... Send $tu command within 30 seconds.')
        try:
            await client.wait_for('message', check=parse_tu, timeout=30)
        except TimeoutError:
            logging.critical('Could not parse $tu command, quitting (try again)')
            browser.close()
            await close_bot()
        else:
            logging.info('$tu command parsed')
            logging.info('Creating new Timer based on parsed information')
            timer = Timer(browser, timing_info["claim_reset"], timing_info["rolls_reset"], timing_info["daily_reset"],
                          timing_info['claim_available'], timing_info["kakera_reset"], timing_info["kakera_available"])

            if config.DAILY_DURATION > 0:
                threading.Thread(name='daily', target=timer.wait_for_daily).start()
            if config.ROLL_DURATION > 0:
                threading.Thread(name='roll', target=timer.wait_for_roll).start()
            threading.Thread(name='claim', target=timer.wait_for_claim).start()
            threading.Thread(name='kakera', target=timer.wait_for_kakera).start()

            # For some reason, browser Discord crashes sometime at this point
            # Refresh the page to fix
            browser.refresh()  # Blocking call
            logging.info("Listener is ready")
            ready = True


@client.event
async def on_message(message):
    def parse_embed():
        # Regex based parsing adapted from the EzMudae module by Znunu
        # https://github.com/Znunu/EzMudae
        desc = embed.description
        name = embed.author.name
        series = None
        owner = None
        key = False

        # Get series and key value if present
        match = re.search(r'^(.*?[^<]*)(?:<:(\w+key))?', desc, re.DOTALL)
        if match:
            series = match.group(1).replace('\n', ' ').strip()
            if len(match.groups()) == 3:
                key = match.group(2)

        # Check if it was a roll
        # Look for stars in embed (Example: **47**)
        match = re.search(r'(?<=\*)(\d+)', desc, re.DOTALL)
        if match:
            pass

        # Look for picture wheel (Example: 1/31)
        # match = re.search(r'(?<=\d)(\/)', desc, re.DOTALL) doesn't find

        match = re.search(r'(:female:|:male:)', desc, re.DOTALL)
        if match:
            return

        # Check if valid parse
        if not series:
            return

        # Get owner if present
        if not embed.footer.text:
            is_claimed = False
        else:
            match = re.search(r'(?<=Belongs to )\w+', embed.footer.text, re.DOTALL)
            if match:
                is_claimed = True
                owner = match.group(0)
            else:
                is_claimed = False

        # Log in roll list and console/logfile
        with open('waifu_list/rolled.txt', 'a') as f:
            f.write(f'{datetime.datetime.now()}    {name} - {series}\n')

        logging.info(f'Parsed roll: {name} - {series} - Claimed: {is_claimed}')

        return {'name': name,
                'series': series,
                'is_claimed': is_claimed,
                'owner': owner,
                'key': key}

    def reaction_check(payload):
        # Return if reaction message or author incorrect
        if payload.message_id != message.id:
            return
        if payload.user_id != mudae.id:
            return

        # Open thread to click emoji
        emoji = payload.emoji
        pool.submit(browser.react_emoji, emoji.name, message.id)
        return True

    def parse_user_input(message):
        pass

    # BEGIN ON_MESSAGE BELOW #
    global main_user, mudae, dm_channel, roll_channel, ready
    if not ready:
        return

    if message.channel == roll_channel and message.author == main_user:
        if message.content.startswith("$quit"):
            logging.critical("User Stopping Bot")
            try:
                browser.close()
            except:
                client.loop.stop()
                client.loop.close()
            finally:
                client.loop.run_until_complete(client.logout())

    # Only parse messages from the bot in the right channel that contain a valid embed
    if message.channel != roll_channel or message.author != mudae or not len(message.embeds) == 1 or \
            message.embeds[0].image.url == message.embeds[0].Empty:
        return
    # Check for user input

    embed = message.embeds[0]
    if not (waifu_result := parse_embed()):
        return  # Return if parsing failed
    browser.set_character(waifu_result['name'])

    # If unclaimed waifu was on likelist
    if not waifu_result['is_claimed'] and timer.get_claim_availability() and waifu_result['name'] in love_array:
        pool.submit(browser.attempt_claim)
        logging.info(f'{waifu_result["name"]} in lovelist')
        logging.info(f'Character {waifu_result["name"]} in lovelist, attempting marry')
        await dm_channel.send(content=f"{waifu_result['name']} is in the lovelist"
                                      f"Attempted to marry", embed=embed)

    if waifu_result['name'] in like_array and not waifu_result['is_claimed']:
        await dm_channel.send(content=f"Character {waifu_result['name']} is in the likelist:"
                              f"\nhttps://discord.com/channels/{config.SERVER_ID}/{config.CHANNEL_ID}\n", embed=embed)

    if waifu_result['name'] not in like_array or love_array:
        browser.set_im_state(True)
        if config.TEST_REACT:
            pool.submit(browser.attempt_claim)

    # If key was rolled
    if waifu_result['owner'] == main_user.name and waifu_result['key']:
        await dm_channel.send(content=f"{waifu_result['key']} rolled for {waifu_result['name']}", embed=embed)

    # If kakera loot available
    if waifu_result['is_claimed'] and timer.get_kakera_availablilty():
        logging.info(f'Character {waifu_result["name"]} has kakera loot...')
        logging.info('Attempting to loot kakera')
        try:
            await client.wait_for('raw_reaction_add', check=reaction_check, timeout=10)
        except TimeoutError:
            logging.critical('Kakera loot failed, could not detect bot reaction')
            return
        else:
            await dm_channel.send(content=f"Kakera loot attempted for {waifu_result['name']}", embed=embed)
            timer.set_kakera_availability(False)


if __name__ == '__main__':
    with open('waifu_list/lovelist.txt', 'r') as f:
        logging.info('Parsing lovelist')
        love_array = tuple({x.strip() for x in [x for x in f.readlines() if not x.startswith('\n')] if not x.startswith('#')})
        logging.info(f'Current lovelist: {love_array}')

    with open('waifu_list/likelist.txt', 'r') as f:
        logging.info('Parsing likelist')
        like_array = tuple({x.strip() for x in [x for x in f.readlines() if not x.startswith('\n')] if not x.startswith('#')})
        logging.info(f'Current likelist: {like_array}')

    pool = ThreadPoolExecutor()
    try:
        logging.info('Starting browser thread')
        browser_login = pool.submit(Browser.browser_login, browser)
        client.loop.run_until_complete(client.start(config.BOT_TOKEN))
    except KeyboardInterrupt:
        logging.critical("Keyboard interrupt, quitting")
        client.loop.run_until_complete(client.logout())
    except discord.LoginFailure or aiohttp.ClientConnectorError:
        logging.critical(f"Improper token has been passed or connection to Discord failed, quitting")
    finally:
        browser.close()
        client.loop.stop()
        client.loop.close()
