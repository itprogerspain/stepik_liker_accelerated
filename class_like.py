from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from time import sleep
import random
from class_logger import get_logger

logger = get_logger('class_like')

class Like:
    def __init__(self, raw_like):
        self.raw_like = raw_like
        self.like = None
        self.is_good = False
        try:
            self.solution_url = self.raw_like.find_element(By.CSS_SELECTOR, 'a[data-likeable-type="solution"]').get_attribute('href')
            self.liker_id = self.raw_like.find_element(By.CSS_SELECTOR, 'a[data-author-id]').get_attribute('data-author-id')
            self.is_good = True
        except Exception as e:
            logger.warning(f"Failed to parse like: {str(e)}")

    def get_info(self):
        return self.solution_url, self.liker_id

    def mark_read(self):
        try:
            self.raw_like.find_element(By.CLASS_NAME, 'notification__icon--read').click()
        except Exception as e:
            logger.warning(f"Failed to mark as read: {str(e)}")

    def like(self):
        try:
            self.like = self.raw_like.find_element(By.CLASS_NAME, 'like-button')
            if 'like-button--active' not in self.like.get_attribute('class'):
                self.like.click()
                sleep(random.uniform(1, 3))  # Задержка после лайка
                logger.debug(f'Liked: {self.get_info()}')
        except Exception as e:
            logger.warning(f'Failed to like: {str(e)}')

    def __repr__(self):
        return f'Like(solution_url={self.solution_url}, liker_id={self.liker_id})'

