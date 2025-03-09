from time import sleep
import random

from config import load_config
from load_friends_data import load_friends_data
from class_logger import get_logger
from class_like import Like
from scroll_down import scroll_down

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

logger = get_logger('class_browser')

class MyFirefoxBrowser(webdriver.Firefox):
    __instance = None

    options = FirefoxOptions()
    firefox_path = 'firefox_portable/firefox.exe'  # Убрать для системной версии
    options.binary_location = firefox_path

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, timeout=30):
        firefox_driver_path = "drivers/geckodriver.exe"
        service = FirefoxService(executable_path=firefox_driver_path)
        super().__init__(service=service, options=self.options)
        self.waiter = WebDriverWait(self, timeout)
        self.friends_data = load_friends_data()
        self._do_login()

    def _do_login(self):
        user = load_config()
        self.get('https://stepik.org')
        try:
            self.waiter.until(EC.presence_of_element_located((By.CLASS_NAME, 'navbar__auth_login'))).click()
        except TimeoutException:
            logger.warning("Login button not found, possibly already logged in")
            pass  # Пропускаем, если уже авторизованы

        name_field = self.waiter.until(EC.presence_of_element_located((By.ID, 'id_login_email')))
        pwd_field = self.waiter.until(EC.presence_of_element_located((By.ID, 'id_login_password')))
        enter_btn = self.find_element(By.CLASS_NAME, 'sign-form__btn')

        name_field.send_keys(user.username)
        pwd_field.send_keys(user.password)
        enter_btn.click()
        sleep(2)

        try:
            self.waiter.until(EC.presence_of_element_located((By.CLASS_NAME, 'navbar__profile-toggler')))
            logger.info("Login successful")
        except TimeoutException:
            logger.error("Login failed, navbar__profile-toggler not found")
            raise

        self.cookies = self.get_cookies()
        self._finish_login()

    def _finish_login(self):
        self.find_element(By.CLASS_NAME, 'navbar__profile-toggler').click()
        user_profile = self.waiter.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-qa='menu-item-profile']")))
        *_, self.STEPIK_SELF_ID, _ = user_profile.find_element(By.TAG_NAME, 'a').get_attribute('href').split('/')
        sleep(1)

    def open_new_tab(self, url):
        self.execute_script(f'window.open("{url}", "_blank");')
        self.switch_to.window(self.window_handles[-1])
        self.delete_all_cookies()
        for cookie in self.cookies:
            self.add_cookie(cookie)
        self.refresh()
        try:
            self.waiter.until(EC.presence_of_element_located((By.CLASS_NAME, 'navbar__profile-toggler')))
            logger.debug(f"Authentication transferred to new tab for {url}")
        except TimeoutException:
            logger.error(f"Authentication failed on new tab for {url}")
            raise

    def go_to_notifications(self):
        self.get('https://stepik.org/notifications?type=comments')
        sleep(1)
        initial_notifications = self.waiter.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'notifications__widget')))
        last_len = len(initial_notifications)
        for _ in range(5):
            scroll_down(self, str(last_len * 2), logger)
            new_notifications = self.waiter.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'notifications__widget')))
            current_len = len(new_notifications)
            if current_len == last_len:
                break
            last_len = current_len
            sleep(1)
        return new_notifications

    def like_comment(self):
        try:
            like_buttons = self.waiter.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'attempt-status__like-button')))
            for button in like_buttons:
                if not button.is_selected():
                    button.click()
                    logger.debug(f'Liked a comment on {self.current_url}')
                    sleep(random.uniform(0.3, 0.7))
        except Exception as e:
            logger.warning(f'Could not find like buttons: {e}')

class MyChromeBrowser(webdriver.Chrome):
    __instance = None

    options = ChromeOptions()
    options.add_argument('--disable-site-isolation-trials')

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, timeout=30):
        chrome_driver_path = "drivers/chromedriver.exe"
        service = ChromeService(executable_path=chrome_driver_path)
        super().__init__(service=service, options=self.options)
        self.waiter = WebDriverWait(self, timeout)
        self.friends_data = load_friends_data()
        self._do_login()

    def _do_login(self):
        user = load_config()
        self.get('https://stepik.org')
        try:
            self.waiter.until(EC.presence_of_element_located((By.CLASS_NAME, 'navbar__auth_login'))).click()
        except TimeoutException:
            logger.warning("Login button not found, possibly already logged in")
            pass

        name_field = self.waiter.until(EC.presence_of_element_located((By.ID, 'id_login_email')))
        pwd_field = self.waiter.until(EC.presence_of_element_located((By.ID, 'id_login_password')))
        enter_btn = self.find_element(By.CLASS_NAME, 'sign-form__btn')

        name_field.send_keys(user.username)
        pwd_field.send_keys(user.password)
        enter_btn.click()
        sleep(2)

        try:
            self.waiter.until(EC.presence_of_element_located((By.CLASS_NAME, 'navbar__profile-toggler')))
            logger.info("Login successful")
        except TimeoutException:
            logger.error("Login failed, navbar__profile-toggler not found")
            raise

        self.cookies = self.get_cookies()
        self._finish_login()

    def _finish_login(self):
        self.find_element(By.CLASS_NAME, 'navbar__profile-toggler').click()
        user_profile = self.waiter.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-qa='menu-item-profile']")))
        *_, self.STEPIK_SELF_ID, _ = user_profile.find_element(By.TAG_NAME, 'a').get_attribute('href').split('/')
        sleep(1)

    def open_new_tab(self, url):
        self.execute_script(f'window.open("{url}", "_blank");')
        self.switch_to.window(self.window_handles[-1])
        self.delete_all_cookies()
        for cookie in self.cookies:
            self.add_cookie(cookie)
        self.refresh()
        try:
            self.waiter.until(EC.presence_of_element_located((By.CLASS_NAME, 'navbar__profile-toggler')))
            logger.debug(f"Authentication transferred to new tab for {url}")
        except TimeoutException:
            logger.error(f"Authentication failed on new tab for {url}")
            raise

    def go_to_notifications(self):
        self.get('https://stepik.org/notifications?type=comments')
        sleep(1)
        initial_notifications = self.waiter.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'notifications__widget')))
        last_len = len(initial_notifications)
        for _ in range(5):
            scroll_down(self, str(last_len * 2), logger)
            new_notifications = self.waiter.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'notifications__widget')))
            current_len = len(new_notifications)
            if current_len == last_len:
                break
            last_len = current_len
            sleep(1)
        return new_notifications

    def like_comment(self):
        try:
            like_buttons = self.waiter.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'attempt-status__like-button')))
            for button in like_buttons:
                if not button.is_selected():
                    button.click()
                    logger.debug(f'Liked a comment on {self.current_url}')
                    sleep(random.uniform(1, 2))
        except Exception as e:
            logger.warning(f'Could not find like buttons: {e}')

# Можно выбрать Chrome или Firefox
# MyBrowser = MyFirefoxBrowser
MyBrowser = MyChromeBrowser

if __name__ == '__main__':
    with MyBrowser() as browser:
        notifications = browser.go_to_notifications()
        print(f"Found {len(notifications)} notifications")
