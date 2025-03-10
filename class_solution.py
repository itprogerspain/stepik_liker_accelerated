from selenium.webdriver.remote.webelement import WebElement
from time import sleep
import random
from selenium.webdriver.common.by import By
from class_logger import get_logger

logger = get_logger('class_solution')

class Solution:
    def __init__(self, raw_solution):
        self.sol = raw_solution
        self.voted = False
        self.user_id = self.sol.get_attribute('data-author-id')
        try:
            like_button = self.sol.find_element(By.CLASS_NAME, 'like-button')
            if 'like-button--active' in like_button.get_attribute('class'):
                self.voted = True
        except Exception as e:
            logger.warning(f"Failed to check if solution is liked: {str(e)}")

    def like(self):
        try:
            like_button = self.sol.find_element(By.CLASS_NAME, 'like-button')
            if 'like-button--active' not in like_button.get_attribute('class'):
                like_button.click()
                sleep(random.uniform(1, 3))  # Задержка после лайка
                self.voted = True
                logger.debug(f'Liked solution by user {self.user_id}')
        except Exception as e:
            logger.warning(f'Failed to like solution by user {self.user_id}: {str(e)}')

    def get_statistic_info(self):
        user_name = self.sol.find_element(By.CLASS_NAME, 'comment__user-name').text
        return self.user_id, user_name, 0, 1 if self.voted else 0