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

    # Ожидание загрузки хотя бы одного уведомления
    try:
        WebDriverWait(browser, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-type="like"]'))
        )
    except Exception as e:
        logger.error(f"Failed to load notifications page: {str(e)}")
        return {}

    sleep(random.uniform(2, 4))

    raw_likes = browser.find_elements(By.CSS_SELECTOR, 'div[data-type="like"]')
    n_likes = len(raw_likes)
    if n_likes:
        logger.debug(f'Общее количество лайков: {n_likes}')
        scroll_down(browser, str(n_likes), logger, element_class='notification')
    else:
        logger.info('Нет лайков для обработки')

    raw_likes_list = browser.find_elements(By.CSS_SELECTOR, 'div[data-type="like"]')
    likes_data = {}
    skipped_likes = []  # Список пропущенных лайков для детального логирования
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
            skipped_likes.append({
                'solution_url': like.solution_url,
                'liker_id': like.liker_id,
                'text': raw_like.text if hasattr(raw_like, 'text') else 'No text'
            })
            logger.warning(f'Skipped notification: URL={like.solution_url}, ID={like.liker_id}, Text={raw_like.text}')

    # Детальное логирование пропущенных лайков
    if skipped_likes:
        logger.info(f"Total skipped notifications: {len(skipped_likes)}")
        for i, skipped in enumerate(skipped_likes, 1):
            logger.info(
                f"Skipped {i}/{len(skipped_likes)}: URL={skipped['solution_url']}, ID={skipped['liker_id']}, Text={skipped['text']}")

    stat.dump_data()
    return likes_data