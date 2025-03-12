# Файл: class_browser.py
# Описание: Добавлен метод для получения ID текущего пользователя
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from class_logger import get_logger
import time

logger = get_logger('class_browser')

class MyBrowser:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--disable-notifications")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.waiter = WebDriverWait(self.driver, 10)

    def get(self, url):
        self.driver.get(url)
        logger.debug(f"Navigated to {url}")

    def get_current_user_id(self):
        """Извлекает ID текущего пользователя из профиля."""
        try:
            self.driver.get('https://stepik.org/users/current')
            time.sleep(2)  # Дождёмся загрузки страницы
            user_link = self.driver.find_element(By.CLASS_NAME, 'navbar__profile-link')
            user_url = user_link.get_attribute('href')
            user_id = user_url.split('/')[-1].strip()
            logger.info(f"Current user ID: {user_id}")
            return user_id
        except Exception as e:
            logger.error(f"Failed to get current user ID: {str(e)}")
            return None

    def close(self):
        self.driver.quit()

if __name__ == '__main__':
    browser = MyBrowser()
    browser.get('https://stepik.org')
    user_id = browser.get_current_user_id()
    print(f"User ID: {user_id}")
    browser.close()