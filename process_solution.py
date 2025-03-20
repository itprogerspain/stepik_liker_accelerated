from selenium.common import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from time import sleep
import random

from class_browser import MyBrowser
from class_like import Like
from class_solution import Solution
from scroll_down import scroll_down
from class_logger import get_logger
from class_statistics import Statistics

logger = get_logger('process_solution')
stat = Statistics()

def process_solution(browser: MyBrowser, solution_url: str, ids_list: list[str] | None = None,
                     likes_list: list[Like] | None = None, total_notifications: int = None) -> tuple[int, int, int]:
    """
    :param browser: браузер
    :param solution_url: адрес страницы с решениями, которые нужно полайкать
    :param ids_list: опционально. список stepik_id для ответных лайков
    :param likes_list: опционально. Список лайков для пометки прочитанными
    :param total_notifications: общее количество уведомлений в сессии
    :return: (количество новых лайков, количество уже лайкнутых, общее количество решений)
    """
    ids_list = ids_list or []
    likes_list = likes_list or []
    STEPIK_SELF_ID = browser.STEPIK_SELF_ID
    friends_data = browser.friends_data

    # Открываем страницу с решениями
    browser.execute_script(f'window.open("{solution_url}", "_blank1");')  # open url in new tab
    browser.switch_to.window(browser.window_handles[-1])  # switch to new tab
    try:
        _ = browser.waiter.until(EC.presence_of_element_located((By.CLASS_NAME, "tab__item-counter")))
    except TimeoutException:
        logger.error(f"Failed to load solution page {solution_url}: tab__item-counter not found")
        # Устанавливаем статус "error" для всех уведомлений, связанных с этой ссылкой
        for like in likes_list:
            stat.update_like_status(like, status="error")
        stat.dump_data()
        browser.close()  # Закрываем вкладку
        browser.switch_to.window(browser.window_handles[0])  # Возвращаемся к основной вкладке
        return 0, 0, 0  # Возвращаем нули, так как обработка не удалась

    sleep(random.uniform(2, 4))

    comments_sols = browser.find_elements(By.CLASS_NAME, "tab__item-counter")
    n_sols = '0'
    if len(comments_sols) == 2:
        comments, sols = comments_sols
        n_sols = sols.get_attribute('data-value')  # количество решений
    logger.debug(f'Общее количество решений: {n_sols}')

    # Динамический скроллинг
    scroll_down(browser, n_sols, logger, element_class='comment-widget')
    raw_solutions = browser.find_elements(By.CLASS_NAME, 'comment-widget')  # собираем все решения на странице

    # Проверяем, есть ли решения
    if not raw_solutions:
        logger.warning(f"No solutions found at {solution_url}")
        # Устанавливаем статус "pending" для всех уведомлений, связанных с этой ссылкой
        for like in likes_list:
            stat.update_like_status(like, status="pending")
        stat.dump_data()
        browser.close()  # Закрываем вкладку
        browser.switch_to.window(browser.window_handles[0])  # Возвращаемся к основной вкладке
        # Помечаем уведомления как прочитанные, так как отсутствие решений — это нормальный случай
        for like in likes_list:
            browser.execute_script("arguments[0].scrollIntoView(true);", like.like)
            like.mark_read()
            logger.debug(f'{repr(like)} was marked')
        return 0, 0, 0

    liked = already_liked = 0
    error_occurred = False  # Флаг для отслеживания ошибок

    for i, raw_sol in enumerate(raw_solutions, 1):
        if not i % 20:
            logger.debug(f'Обработка решения {i} из {len(raw_solutions)}')
        solution = Solution(raw_sol, STEPIK_SELF_ID)
        if solution.user_id == STEPIK_SELF_ID:  # если собственное решение - пропускаем без логирования в skipped_solutions
            continue
        elif solution.voted:  # если уже лайкали - пропускаем
            logger.info(f"Skipping already liked solution by {solution.user_name} (ID: {solution.user_id})")
            already_liked += 1
            stat.set_stat(solution, total_notifications)
            # Устанавливаем статус "done before" для всех соответствующих уведомлений
            for like in likes_list:
                if like.user_id == solution.user_id and like.what_was_liked_url in solution_url:
                    stat.update_like_status(like, status="done before")
        elif solution.user_id in friends_data or solution.user_id in ids_list:
            try:
                browser.execute_script("arguments[0].scrollIntoView(true);", solution.sol)
                solution.like()
                sleep(random.uniform(1, 3))  # Задержка после лайка
                liked += 1
                # Устанавливаем статус "processed" для всех соответствующих уведомлений
                for like in likes_list:
                    if like.user_id == solution.user_id and like.what_was_liked_url in solution_url:
                        stat.update_like_status(like, status="processed")
            except Exception as e:
                logger.error(f"Failed to like solution by {solution.user_name} (ID: {solution.user_id}) at {solution_url}: {str(e)}")
                stat.set_stat(solution, total_notifications, failed=True)
                # Устанавливаем статус "error" для всех соответствующих уведомлений
                for like in likes_list:
                    if like.user_id == solution.user_id and like.what_was_liked_url in solution_url:
                        stat.update_like_status(like, status="error")
                error_occurred = True  # Устанавливаем флаг ошибки
        else:
            stat.set_stat(solution, total_notifications)

    stat.dump_data()

    page_title = browser.execute_script("return document.title;")
    solution_count = len(raw_solutions)
    logger.info(f'{page_title} ({solution_url}). Всего решений {solution_count}')
    logger.info(f'Новых лайков: {liked}, старых лайков: {already_liked}')

    sleep(1)  # Задержка перед закрытием страницы для полной загрузки
    browser.close()  # Закрываем вкладку
    browser.switch_to.window(browser.window_handles[0])  # Возвращаемся к основной вкладке

    # Помечаем уведомления как прочитанные, только если не было ошибок
    for like in likes_list:
        # Проверяем статус уведомления
        status = next((entry['status'] for entry in stat.current_session_likes if entry['user_id'] == like.user_id and entry['url'] == like.what_was_liked_url), None)
        if status != "error":  # Не помечаем как прочитанное, если статус "error"
            browser.execute_script("arguments[0].scrollIntoView(true);", like.like)
            like.mark_read()
            logger.debug(f'{repr(like)} was marked')
        else:
            logger.debug(f'Skipping mark_read for {repr(like)} due to error status')

    return liked, already_liked, len(raw_solutions)

if __name__ == '__main__':
    url = 'https://stepik.org/lesson/361657/step/3?thread=solutions'
    list_stepik_ids = []  # список айди, которые будут облайканы (помимо списка друзей)
    browser = MyBrowser()
    process_solution(browser, url, list_stepik_ids)