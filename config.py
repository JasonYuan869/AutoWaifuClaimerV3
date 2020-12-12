# EDIT THE CONFIG HERE #
# Replace values with your own
MUDAE_ID = 432610292342587392  # ID of Mudae bot
CHANNEL_ID = 432610292342587392  # ID of claiming channel
SERVER_ID = 432610292342587392  # ID of Discord server
USER_ID = 432610292342587392  # ID of main user
BOT_TOKEN = ""  # Bot token
COMMAND_PREFIX = "$"
ROLL_COMMAND = "m"
LOGIN_INFO = ("example@example.com", "password")
CLAIM_DURATION = 180  # in minutes
ROLL_DURATION = 60  # in minutes
DAILY_DURATION = 1200  # in minutes
KAKERA_DURATION = 60  # in minutes, set to 0 to always attempt kakera loot
MAX_ROLLS = 10  # in minutes
ALWAYS_ROLL = False  # Set True to roll every interval despite having claims or not

LOG_FILE = "./log.txt"

# SELENIUM CONFIG INFO #
# On Ubuntu, run:
# $ sudo apt update
# $ sudo apt install geckodriver
# On Windows, download from https://github.com/mozilla/geckodriver/releases and extract
WEB_DRIVER_PATH = "/usr/bin/geckodriver"
