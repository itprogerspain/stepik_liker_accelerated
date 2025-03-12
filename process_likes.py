# Файл: process_likes.py
# Описание: Добавлено логирование пропущенных уведомлений
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

from selenium.common import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

logger = get_logger('process_likes')
stat = Statistics()


def process_likes(browser: MyBrowser):
    notifications_url = 'https://stepik.org/notifications?type=comments'
    browser.get(notifications_url)
    browser.waiter.until(EC.presence_of_element_located((By.CLASS_NAME, 'navbar__profile-toggler')))
    sleep(2)

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

    # Фильтруем лайки
    raw_likes_list = [notif for notif in all_notifications if 'data-action="liked"' in notif.get_attribute('outerHTML')]
    n_likes = len(raw_likes_list)
    logger.info(f'Total number of like notifications: {n_likes}')

    likes_data_vals = lambda: {'ids_list': [], 'likes_list': []}
    likes_data = defaultdict(likes_data_vals)

    skipped_notifications = []  # Список пропущенных уведомлений

    for i, raw_notification in enumerate(all_notifications, 1):
        if not i % 10:
            logger.debug(f'Processing notification {i} of {n_notifications_after_scroll}')

        # Проверяем, является ли уведомление лайком
        if 'data-action="liked"' not in raw_notification.get_attribute('outerHTML'):
            skipped_notifications.append({
                'text': raw_notification.text,
                'reason': 'Not a like notification (e.g., advertisement or other type)',
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            logger.warning(f'Skipped non-like notification: Text={raw_notification.text}')
            continue

        like = Like(raw_notification)
        if like.is_good:
            solution_url, liker_id = like.get_info()
            val = likes_data[solution_url]
            val['ids_list'].append(liker_id)
            val['likes_list'].append(like)
            stat.set_stat(like)
        else:
            like.mark_read()
            skipped_notifications.append({
                'solution_url': like.what_was_liked_url,
                'liker_id': like.user_id,
                'liker_name': like.user_name,
                'text': raw_notification.text,
                'reason': 'Like notification without a published solution or other issue',
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            logger.warning(
                f'Skipped like notification: URL={like.what_was_liked_url}, ID={like.user_id}, Name={like.user_name}, Text={raw_notification.text}')

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

    stat.dump_data()
    return likes_data


if __name__ == '__main__':
    browser = MyBrowser()
    likes_data = process_likes(browser)
    print(f'len = {len(likes_data)}')
