# Файл: process_likes.py
# Описание: Исправлен и восстановлен автоматический логин с улучшенной обработкой
from collections import defaultdict
from class_browser import MyBrowser
from time import sleep
from class_logger import get_logger
from scroll_down import scroll_down
from class_like import Like
from class_statistics import Statistics
import json
from pathlib import Path
import datetime

from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from config import EMAIL, PASSWORD  # Импортируем учётные данные

logger = get_logger('process_likes')
stat = Statistics()


def process_likes(browser: MyBrowser):
    # Проверяем, авторизован ли пользователь
    browser.get('https://stepik.org')
    sleep(2)  # Даём странице загрузиться

    try:
        # Ждём кнопку "Войти" (ожидание до 10 секунд)
        login_button = browser.waiter.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Войти')))
        logger.info("User not logged in, attempting to log in")

        # Переходим на страницу логина
        login_button.click()
        sleep(2)

        # Ждём поля логина и пароля
        try:
            # Обновлённые селекторы для полей логина и пароля
            email_field = browser.waiter.until(EC.presence_of_element_located((By.ID, 'id_login_email')))
            password_field = browser.waiter.until(EC.presence_of_element_located((By.ID, 'id_login_password')))
            submit_button = browser.waiter.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.sign-form__btn')))

            # Вводим логин и пароль
            email_field.clear()  # Очищаем поле перед вводом
            email_field.send_keys(EMAIL)
            password_field.clear()  # Очищаем поле перед вводом
            password_field.send_keys(PASSWORD)
            submit_button.click()
            sleep(3)  # Ждём, пока логин завершится

            # Проверяем, что логин успешен
            browser.get('https://stepik.org')
            sleep(2)
            if "Войти" in browser.driver.page_source:
                raise Exception("Login failed, please check your credentials in config.py")
            logger.info("Successfully logged in")
        except TimeoutException as e:
            logger.error(f"Failed to find login form elements: {str(e)}")
            with open('debug_login_page.html', 'w', encoding='utf-8') as f:
                f.write(browser.driver.page_source)
            logger.info("Saved login page source to debug_login_page.html for inspection")
            raise
    except TimeoutException:
        logger.info("User already logged in or login button not found")

    # Переходим на страницу уведомлений
    notifications_url = 'https://stepik.org/notifications?type=comments'
    browser.get(notifications_url)
    try:
        browser.waiter.until(EC.presence_of_element_located((By.CLASS_NAME, 'navbar__profile-toggler')))
        sleep(2)
    except TimeoutException as e:
        logger.error(f"Failed to load notifications page: {str(e)}")
        # Проверяем, что на странице
        if "Войти" in browser.driver.page_source:
            logger.error("Redirected to login page, login might have failed")
        elif "503" in browser.driver.page_source:
            logger.error("Stepik returned 503 Service Unavailable")
        else:
            logger.error("Unknown issue, page source might have changed")
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(browser.driver.page_source)
            logger.info("Saved page source to debug_page.html for inspection")
        raise

    # Получаем ID текущего пользователя
    current_user_id = browser.get_current_user_id()
    if not current_user_id:
        logger.error("Could not determine current user ID, skipping ownership check")
        current_user_id = None

    try:
        n_events = browser.waiter.until(EC.presence_of_element_located((By.ID, 'profile-notifications-badge'))).text
    except NoSuchElementException:
        logger.warning('Нет лайков, или количество не прогрузилось')
        n_events = '0'

    logger.info(f'Number of events: {n_events}')

    # Собираем все уведомления
    all_notifications = browser.find_elements(By.CLASS_NAME, 'notifications__widget')
    n_notifications = len(all_notifications)
    if n_notifications:
        logger.debug(f'Initial number of notifications: {n_notifications}')
        scroll_down(browser, n_events, logger, element_class='notifications__widget')
    else:
        logger.info('No notifications found')

    # Обновляем список уведомлений после прокрутки
    all_notifications = browser.find_elements(By.CLASS_NAME, 'notifications__widget')
    n_notifications_after_scroll = len(all_notifications)
    logger.debug(f'Number of notifications after scroll: {n_notifications_after_scroll}')

    # Фильтруем лайки (решений и комментариев)
    raw_likes_list = []
    skipped_notifications = []
    for raw_notification in all_notifications:
        notification_text = raw_notification.text.encode("utf-8", errors="replace").decode("utf-8")
        if ('data-action="liked"' in raw_notification.get_attribute('outerHTML') or
                "оценил(а) ваше решение" in notification_text or
                "оценил(а) ваш комментарий к решению" in notification_text):
            raw_likes_list.append(raw_notification)
        else:
            skipped_notifications.append({
                'text': notification_text,
                'reason': 'Not a like notification (e.g., advertisement or other type)',
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            logger.warning(f'Skipped non-like notification: Text={notification_text}')

    n_likes = len(raw_likes_list)
    logger.info(f'Total number of like notifications: {n_likes}')

    likes_data_vals = lambda: {'ids_list': [], 'likes_list': []}
    likes_data = defaultdict(likes_data_vals)

    for i, raw_notification in enumerate(raw_likes_list, 1):
        if not i % 10:
            logger.debug(f'Processing like notification {i} of {n_likes}')

        notification_text = raw_notification.text.encode("utf-8", errors="replace").decode("utf-8")
        like = Like(raw_notification)
        if like.is_good:
            solution_url, liker_id = like.get_info()
            if "оценил(а) ваш комментарий к решению" in notification_text:
                logger.info(f'Processing comment like from {like.user_name} (ID: {liker_id}) for URL: {solution_url}')
                stat.increment_comment_likes()
            else:
                logger.info(f'Processing solution like from {like.user_name} (ID: {liker_id}) for URL: {solution_url}')
                stat.increment_solution_likes()
            val = likes_data[solution_url]
            val['ids_list'].append(liker_id)
            val['likes_list'].append(like)
            stat.set_stat(like)
        else:
            like.mark_read()
            # Проверяем, является ли решение собственным, чтобы исключить из skipped_solutions
            is_own_solution = False
            if current_user_id and like.what_was_liked_url:
                try:
                    browser.get(like.what_was_liked_url)
                    sleep(2)
                    author_id = \
                    browser.find_element(By.CLASS_NAME, 'attempt__user-link').get_attribute('href').split('/')[
                        -1].strip()
                    if author_id == current_user_id:
                        is_own_solution = True
                        logger.info(f'Skipped own solution: {like.what_was_liked_url} by {like.user_name}')
                except Exception as e:
                    logger.error(f'Failed to check solution ownership for {like.what_was_liked_url}: {str(e)}')

            if not is_own_solution:
                skipped_notifications.append({
                    'solution_url': like.what_was_liked_url,
                    'liker_id': like.user_id,
                    'liker_name': like.user_name,
                    'text': notification_text,
                    'reason': 'Like notification without a published solution or other issue',
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                logger.warning(
                    f'Skipped like notification: URL={like.what_was_liked_url}, ID={like.user_id}, Name={like.user_name}, Text={notification_text}')
                stat.skipped_solutions.append({
                    'url': like.what_was_liked_url,
                    'reason': 'Not a valid solution or already liked'
                })

    # Сохраняем пропущенные уведомления
    if skipped_notifications:
        logger.info(f"Total skipped notifications: {len(skipped_notifications)}")
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        skipped_log_file = log_dir / "skipped_notifications.json"
        try:
            with open(skipped_log_file, 'w', encoding='utf-8') as f:
                json.dump(skipped_notifications, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved skipped notifications to {skipped_log_file}")
        except Exception as e:
            logger.error(f"Failed to save skipped notifications to {skipped_log_file}: {str(e)}")

    # Сохраняем статистику
    stat.dump_data()
    return likes_data


if __name__ == '__main__':
    browser = MyBrowser()
    likes_data = process_likes(browser)
    print(f'len = {len(likes_data)}')