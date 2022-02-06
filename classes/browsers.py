import logging
import time
from asyncio import TimeoutError
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from config import config


class Browser:
    def __init__(self):
        """
        Represents a Selenium browser object with added functions for Discord-specific purposes.
        No parameters; global settings are used from config.py.

        Methods
        -----------
        browser_login()
            Opens the browser to the Discord channel and logs in if necessary.
            Returns True if load successful.
            Raises TimeoutError if the page does not load.
            Raises ValueError if incorrect page loads.
        send_text(text)
            Send text to active channel.
        react_emoji(emoji, message_id)
            Searches and clicks an emoji button.
            Raises Exception if button was not found.
        roll(count)
            Sends the roll command for count number of times with 3 seconds between each roll.
        refresh()
            Refreshes the page.
        close()
            Closes the browser window.
        """
        # Selenium browser control here
        options = Options()
        if config.HEADLESS:
            options.add_argument('-headless')
        # self.driver = webdriver.Firefox(executable_path=config.WEB_DRIVER_PATH, options=options)
        self.driver = webdriver.Remote(command_executor=config.WEB_DRIVER_PATH, options=options)
        self.actions = ActionChains(self.driver)
        # Logging initialization
        self.logger = logging.getLogger(__name__)
        self.character = str()
        self.im_state = bool

    # Initiate browser
    def browser_login(self):
        self.logger.info('Browser thread started')
        self.logger.info('Attempting to open Discord in browser')
        self.driver.get(f'https://discord.com/channels/{config.SERVER_ID}/{config.CHANNEL_ID}')
        try:
            email = WebDriverWait(self.driver, 10).until(lambda x: x.find_element(By.NAME, 'email'))
        except TimeoutException:
            if f'{config.SERVER_ID}/{config.CHANNEL_ID}' not in self.driver.current_url:
                # No login screen, but wrong channel (some weird error)
                self.logger.critical('The channel did not load and no login was asked!')
                raise TimeoutError
        else:
            self.logger.info('Logging in with provided credentials (this may take up to 30 seconds)')
            email.send_keys(config.LOGIN_INFO[0])
            self.driver.find_element(By.NAME, 'password').send_keys(config.LOGIN_INFO[1])
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            try:
                # Wait for main screen
                WebDriverWait(self.driver, 15).until(lambda x: x.find_element(By.CLASS_NAME, 'textAreaSlate-9-y-k2'))
                if f'{config.SERVER_ID}/{config.CHANNEL_ID}' not in self.driver.current_url:
                    # Logged in, but wrong channel (some weird error)
                    raise ValueError
            except TimeoutException or NoSuchElementException:
                self.logger.critical('Login was unsuccessful. Please check LOGIN_INFO entry in config.py')
                raise TimeoutError
            except ValueError:
                self.logger.critical('Login was successful but the channel did not load')
                raise ValueError
            else:
                self.logger.info(f'Login successful to server {config.SERVER_ID} and channel {config.CHANNEL_ID}')
                return True

    def send_text(self, text: str):
        # For some reason, typing directly into the message box doesn't work
        # ActionChains must be used instead to type character by character
        self.actions = ActionChains(self.driver)
        self.logger.info(f'Sending text: {text}')
        try:
            message_box = WebDriverWait(self.driver, 5).until(
                lambda x: x.find_element(By.CLASS_NAME, 'textAreaSlate-9-y-k2'))
        except TimeoutException:
            self.logger.warning("Discord may have crashed, refreshing page")
            self.refresh()
            return self.send_text(text)
        self.actions.click(on_element=message_box)
        for char in text:
            self.actions.key_down(char)
            self.actions.key_up(char)
        self.actions.key_down(Keys.ENTER)
        self.actions.key_up(Keys.ENTER)
        self.actions.perform()

    def react_emoji(self, reaction: str, message_id: int):
        self.logger.info(f'Attempting to click: {reaction}')
        xpath = f"//*[@id='chat-messages-{message_id}']//*[@id='message-accessories-{message_id}']//*[div]//*[div]//*[div]//*[div]//*[div]"
        time.sleep(config.INSTANT_REACT_SPEED)
        try:
            # Get div containing emoji
            emoji_div = WebDriverWait(self.driver, 7).until(lambda x: x.find_element(By.XPATH, xpath))
            # Get current count
            count = 1
            # Click emoji
            # WebElement.click() breaks for some reason, use javascript instead
            self.driver.execute_script('arguments[0].click();', emoji_div)

            # Check new count
            try:
                WebDriverWait(self.driver, 4) \
                    .until_not(lambda x:
                               int(x.find_element(By.XPATH,
                                                  f"{xpath}//div").text) > count)
            except TimeoutException:  # No increase in count
                self.logger.warning('Emoji was found, but unsuccessfully clicked')
                raise TimeoutError
            else:
                self.logger.info('Emoji successfully clicked')
        except TimeoutException or NoSuchElementException:
            self.logger.critical('Unable to find the emoji to click')
            raise TimeoutError

    def attempt_claim(self):
        emoji = f"+{config.CLAIM_EMOJI}" #add : if only showing part of the word
        time.sleep(config.INSTANT_CLAIM_SPEED)
        self.send_text(emoji)

    def determine_im(self):
        if self.im_state:
            self.send_im()
            self.set_im_state(False)
        time.sleep(15)

    def roll(self, count: int):
        """
        Rolls for count number of times.
        """
        for _ in range(count):
            self.send_text(f'{config.COMMAND_PREFIX}{config.ROLL_COMMAND}')
            time.sleep(8)  # Sleep between roll commands
            self.determine_im()
            time.sleep(4)

    def send_im(self):
        self.send_text(f'$im {self.character}')

    def set_character(self, character):
        self.character = character

    def set_im_state(self, boolean):
        self.im_state = boolean

    def refresh(self):
        self.driver.refresh()
        WebDriverWait(self.driver, 10).until(
            lambda x: x.find_element(By.CLASS_NAME, 'textAreaSlate-9-y-k2'))

    def close(self):
        self.driver.quit()
