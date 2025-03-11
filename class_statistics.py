# Файл: class_statistics.py
# Описание: Добавлены счётчики сессии и метод get_session_stats
from class_logger import get_logger
import json
from pathlib import Path
from class_like import Like
from class_solution import Solution

logger = get_logger('class_statistics')

class Statistics:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, stat_file_name='like_stats.json'):
        self.stat_file_name = stat_file_name
        self.stat_data = {}
        # Инициализация счётчиков сессии
        self.liked = 0
        self.skipped = 0
        self.already_liked = 0
        self.processed_solutions = 0
        self.__load_data()

    def __load_data(self):
        if not Path(self.stat_file_name).exists():
            with open(self.stat_file_name, 'w') as f:
                json.dump({}, f)
        else:
            with open(self.stat_file_name, encoding='utf-8') as f:
                self.stat_data = json.load(f)

    def dump_data(self):
        """Сохранение файла статистики"""
        with open(self.stat_file_name, 'w', encoding='utf-8') as f:
            logger.info(f'stat data was saved')
            json.dump(self.stat_data, f, ensure_ascii=False, indent=4)

    def set_stat(self, item: Solution | Like):
        """Статистика. Можно будет глянуть, как менялись имена у лайкавших / лайкнутых айдишников"""
        new_values = lambda: {'names': [], 'likes_from': 0, 'likes_to': 0}
        user_id, user_name, like_from, like_to = item.get_statistic_info()
        logger.debug(f'{user_id}, {user_name}, {like_from}, {like_to}')
        data = self.stat_data.get(user_id, new_values())
        if user_name not in data['names']:
            data['names'].append(user_name)
        data['likes_from'] += like_from
        data['likes_to'] += like_to
        self.stat_data[user_id] = data
        # Обновляем счётчики сессии
        if isinstance(item, Like):
            self.liked += like_from

    def mark_skipped(self):
        self.skipped += 1

    def mark_already_liked(self):
        self.already_liked += 1

    def add_processed_solutions(self, n):
        self.processed_solutions += n

    def get_session_stats(self):
        """Возвращает статистику текущей сессии"""
        return {
            "liked": self.liked,
            "skipped": self.skipped,
            "already_liked": self.already_liked,
            "processed_solutions": self.processed_solutions
        }

if __name__ == '__main__':
    ...

