# Файл: class_like.py
# Описание: Улучшена обработка URL для комментариев
from selenium.webdriver.remote.webelement import WebElement
from class_logger import get_logger
from time import sleep
import random

logger = get_logger('class_like')

class Like:
    def __init__(self, raw_notification: WebElement):
        self.raw_notification = raw_notification
        self.notification_text = raw_notification.text.encode("utf-8", errors="replace").decode("utf-8")
        self.user_name = self._extract_user_name()
        self.user_id = self._extract_user_id()
        self.what_was_liked_url = self._extract_solution_or_comment_url()
        self.like = None
        self.is_good = self._check_is_good()

    def _extract_user_name(self):
        if "оценил(а) ваше решение" in self.notification_text:
            return self.notification_text.split("оценил(а) ваше решение")[0].strip()
        elif "оценил(а) ваш комментарий к решению" in self.notification_text:
            return self.notification_text.split("оценил(а) ваш комментарий к решению")[0].strip()
        return None

    def _extract_user_id(self):
        try:
            user_link = self.raw_notification.find_element(By.CLASS_NAME, 'notifications__user-name')
            return user_link.get_attribute('href').split('/')[-1].strip()
        except:
            return None

    def _extract_solution_or_comment_url(self):
        try:
            link = self.raw_notification.find_element(By.TAG_NAME, 'a')
            url = link.get_attribute('href')
            # Если это комментарий, нужно извлечь URL родительского решения
            if "оценил(а) ваш комментарий к решению" in self.notification_text:
                # Здесь можно парсить URL для перехода к решению (например, убрать часть комментария)
                # Пока предполагаем, что URL ведёт к странице решения
                return url
            return url
        except:
            return None

    def _check_is_good(self):
        return self.what_was_liked_url is not None and self.user_id is not None

    def get_info(self):
        return self.what_was_liked_url, self.user_id

    def mark_read(self):
        try:
            self.raw_notification.click()
            sleep(random.uniform(1, 2))
            logger.debug(f'Marked as read: {self.user_name} ({self.user_id})')
        except Exception as e:
            logger.error(f'Failed to mark as read for {self.user_name} ({self.user_id}): {str(e)}')

    def __repr__(self):
        return f'Like(user={self.user_name}, id={self.user_id}, url={self.what_was_liked_url})'

if __name__ == '__main__':
    from class_browser import MyBrowser
    browser = MyBrowser()
    browser.get('https://stepik.org/notifications?type=comments')
    sleep(2)
    notifications = browser.find_elements(By.CLASS_NAME, 'notifications__widget')
    if notifications:
        like = Like(notifications[0])
        print(like)
        print(like.get_info())

