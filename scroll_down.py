import logging
from time import sleep
import random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

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
    max_attempts = 15  # Максимальное количество попыток прокрутки (оставляем 15, как у тебя)
    for i in range(max_attempts):
        try:
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(random.uniform(2, 5))  # Оставляем твою задержку для стабильности

            if element_class:
                elements = browser.find_elements(By.CLASS_NAME, element_class)
                current_count = len(elements)
                logger.debug(f"Loaded {current_count}/{n} elements after scroll {i + 1}")
                if current_count >= n or current_count == last_count:  # Останавливаемся, если загружено достаточно или новых элементов нет
                    logger.info(f"Total elements loaded: {current_count} after {i + 1} attempts")
                    break
                last_count = current_count
            else:
                logger.debug(f"Scrolling attempt {i + 1} of {max_attempts}")

        except WebDriverException as e:
            logger.warning(f"Scroll failed on attempt {i + 1}/{max_attempts}: {str(e)}")
            if i == max_attempts - 1:
                logger.error(f"Failed to scroll after {max_attempts} attempts")
                break
            sleep(random.uniform(2, 5))  # Задержка перед повторной попыткой

    return last_count if element_class else None