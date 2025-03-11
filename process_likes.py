from selenium.common import NoSuchElementException
from time import sleep
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from class_browser import MyBrowser
from class_logger import get_logger
from class_like import Like
from class_statistics import Statistics
from scroll_down import scroll_down

logger = get_logger('process_likes')
stat = Statistics()


def process_likes(browser: MyBrowser) -> dict[str, dict[str, list]]:
    browser.get('https://stepik.org/notifications')

    # Ожидание загрузки хотя бы одного уведомления (увеличиваем таймаут до 30 секунд)
    try:
        WebDriverWait(browser, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-type="like"]'))
        )
    except Exception as e:
        logger.error(f"Failed to load notifications page: {str(e)}")
        return {}

    # Дополнительная задержка после загрузки
    sleep(random.uniform(2, 4))

    raw_likes = browser.find_elements(By.CSS_SELECTOR, 'div[data-type="like"]')
    n_likes = len(raw_likes)
    if n_likes:
        logger.debug(f'Общее количество лайков: {n_likes}')
        scroll_down(browser, n_likes, logger, element_class='notification')
    else:
        logger.info('Нет лайков для обработки')

    raw_likes_list = browser.find_elements(By.CSS_SELECTOR, 'div[data-type="like"]')
    likes_data = {}
    for i, raw_like in enumerate(raw_likes_list, 1):
        if not i % 10:
            logger.debug(f'processing raw_like {i} of {len(raw_likes_list)}')
        like = Like(raw_like)
        if like.is_good:
            solution_url, liker_id = like.get_info()
            val = likes_data.setdefault(solution_url, {'ids_list': [], 'likes_list': []})
            val['ids_list'].append(liker_id)
            val['likes_list'].append(like)
            stat.set_stat(like)
        else:
            like.mark_read()
            stat.mark_skipped()
            logger.warning(f'Skipped notification: {raw_like.text}')

    stat.dump_data()
    return likes_data
