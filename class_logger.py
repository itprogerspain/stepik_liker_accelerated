# Файл: class_logger.py
# Описание: Логирование в консоль и файл с улучшенным форматом
import logging
import sys
from pathlib import Path
from config import log_level


def get_logger(name: str, level: str = log_level) -> logging.Logger:
    levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    log_format = '%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'

    logger = logging.getLogger(name)
    logger.setLevel(levels.get(level.upper(), logging.WARNING))

    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(log_format, datefmt='%H:%M:%S')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / f"{name}.log")
        file_formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


if __name__ == '__main__':
    logger = get_logger('test', level='DEBUG')
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warning message')
    print(type(logger))