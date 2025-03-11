from time import sleep
import random
import json
from pathlib import Path
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
    skipped_likes = []
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
                'liker_name': like.liker_name,
                'text': raw_like.text if hasattr(raw_like, 'text') else 'No text'
            })
            logger.warning(
                f'Skipped notification: URL={like.solution_url}, ID={like.liker_id}, Name={like.liker_name}, Text={raw_like.text}')

    if skipped_likes:
        logger.info(f"Total skipped notifications: {len(skipped_likes)}")
        for i, skipped in enumerate(skipped_likes, 1):
            logger.info(
                f"Skipped {i}/{len(skipped_likes)}: URL={skipped['solution_url']}, ID={skipped['liker_id']}, Name={skipped['liker_name']}, Text={skipped['text']}")

        # Сохраняем пропущенные лайки в JSON с перезаписью
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        skipped_log_file = log_dir / "skipped_likes.json"
        try:
            with open(skipped_log_file, 'w', encoding='utf-8') as f:
                json.dump(skipped_likes, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved skipped notifications to {skipped_log_file}")
        except Exception as e:
            logger.error(f"Failed to save skipped notifications to {skipped_log_file}: {str(e)}")

    stat.dump_data()
    return likes_data