import logging
from time import sleep
import random
from selenium.webdriver.common.by import By


def scroll_down(browser, n: str, logger: logging.Logger, element_class: str = None):
    """
    Прокрутка страницы до загрузки всех элементов.
    :param browser: Экземпляр браузера
    :param n: Ожидаемое количество элементов (строка или число)
    :param logger: Логгер
    :param element_class: Класс элементов, которые нужно загрузить (опционально)
    :return: Количество загруженных элементов (или None, если element_class не указан)
    """
    try:
        n = int('0' + n)
    except ValueError:
        n = 1000

    last_count = 0
    max_attempts = 10  # Максимальное количество попыток прокрутки
    for i in range(max_attempts):
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(random.uniform(1, 3))  # Уменьшенная задержка для ускорения
        # sleep(random.uniform(2, 5))
        # sleep(random.uniform(0.5, 1.5))
        # sleep(random.uniform(0.8, 2))

        if element_class:
            elements = browser.find_elements(By.CLASS_NAME, element_class)
            current_count = len(elements)
            logger.debug(f"Loaded {current_count}/{n} elements after scroll {i + 1}")
            if current_count >= n or current_count == last_count:  # Останавливаемся, если загружено достаточно или новых элементов нет
                break
            last_count = current_count
        else:
            logger.debug(f"Scrolling attempt {i + 1} of {max_attempts}")
    return last_count if element_class else None