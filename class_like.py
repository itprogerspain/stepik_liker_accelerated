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
            # Извлекаем имя автора
            self.liker_name = self.raw_like.find_element(By.CLASS_NAME, 'user-name').text
            self.is_good = True
        except Exception as e:
            logger.warning(f"Failed to parse like (URL: {self.solution_url if 'solution_url' in vars(self) else 'N/A'}, "
                          f"ID: {self.liker_id if 'liker_id' in vars(self) else 'N/A'}, "
                          f"Name: {self.liker_name if 'liker_name' in vars(self) else 'N/A'}): {str(e)}")
            self.solution_url = getattr(self, 'solution_url', 'N/A')
            self.liker_id = getattr(self, 'liker_id', 'N/A')
            self.liker_name = getattr(self, 'liker_name', 'N/A')

    def get_info(self):
        return self.solution_url, self.liker_id

    def get_statistic_info(self):
        return self.liker_id, self.liker_name, 1, 0

    def mark_read(self):
        try:
            self.raw_like.find_element(By.CLASS_NAME, 'notification__icon--read').click()
        except Exception as e:
            logger.warning(f"Failed to mark as read (URL: {self.solution_url}, ID: {self.liker_id}, Name: {self.liker_name}): {str(e)}")

    def like(self):
        try:
            self.like = self.raw_like.find_element(By.CLASS_NAME, 'like-button')
            if 'like-button--active' not in self.like.get_attribute('class'):
                self.like.click()
                sleep(random.uniform(1, 3))  # Задержка после лайка
                logger.debug(f'Liked: {self.get_info()} by {self.liker_name}')
        except Exception as e:
            logger.warning(f'Failed to like (URL: {self.solution_url}, ID: {self.liker_id}, Name: {self.liker_name}): {str(e)}')

    def __repr__(self):
        return f'Like(solution_url={self.solution_url}, liker_id={self.liker_id}, liker_name={self.liker_name})'
