from class_logger import get_logger
from time import perf_counter
from process_likes import process_likes
from process_solution import process_solution
from class_browser import MyBrowser
from time import sleep

logger = get_logger('liker_main')

start_time = perf_counter()
total_liked = total_already_liked = total_processed_solutions = 0

with MyBrowser() as browser:
    likes_data = process_likes(browser)  # Собираем лайки
    batch_size = 20  # Обрабатываем по 20 лайков за раз
    solution_urls = []
    for i, (solution_url, like_data) in enumerate(likes_data.items(), 1):
        logger.warning(f'Process solution link {i} of {len(likes_data)}')
        solution_urls.append((solution_url, like_data))
        if i % batch_size == 0 or i == len(likes_data):
            for url, like_data in solution_urls:
                if "Sign Up" not in browser.title and "Pay" not in browser.title:
                    liked, already_liked, n_solutions = process_solution(browser, url, *like_data.values(), total_notifications=len(likes_data))
                    total_liked += liked
                    total_already_liked += already_liked
                    total_processed_solutions += n_solutions
                    logger.info(f'Processed {url}: Liked {liked}, Already liked {already_liked}, Total solutions {n_solutions}')
                else:
                    logger.warning(f'Skipping paid course: {url}')
            solution_urls = []
            sleep(2)  # Пауза между пакетами

end_time = perf_counter()
running_time = end_time - start_time

rest, s = divmod(int(running_time), 60)
h, m = divmod(rest, 60)
spent_time = f'{h}:{m:02d}:{s:02d}'
print()
print(f'Новых лайков {total_liked}, ранее лайкнутых {total_already_liked}')
print(f"Всего обработано: {len(likes_data)} ссылок и {total_processed_solutions} решений")
print(f'Running time {spent_time}')
