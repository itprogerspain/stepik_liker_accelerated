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

    def __init__(self, stat_file_name='like_stats.json', skipped_solutions_file='skipped_solutions.json', skipped_notifications_file='skipped_notifications.json'):
        self.stat_file_name = stat_file_name
        self.skipped_solutions_file = skipped_solutions_file
        self.skipped_notifications_file = skipped_notifications_file
        self.stat_data = {}
        self.skipped_solutions = []
        self.skipped_notifications = []
        self.__load_data()

    def __load_data(self):
        # Перезаписываем all_stats.json при каждом запуске
        with open(self.stat_file_name, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        # Перезаписываем skipped_solutions.json и skipped_notifications.json при каждом запуске
        with open(self.skipped_solutions_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
        with open(self.skipped_notifications_file, 'w', encoding='utf-8') as f:
            json.dump([], f)

    def dump_data(self):
        """Сохранение всех файлов статистики с перезаписью"""
        with open(self.stat_file_name, 'w', encoding='utf-8') as f:
            logger.info(f'Stat data saved to {self.stat_file_name}')
            json.dump(self.stat_data, f, ensure_ascii=False, indent=4)
        with open(self.skipped_solutions_file, 'w', encoding='utf-8') as f:
            logger.info(f'Skipped solutions saved to {self.skipped_solutions_file}')
            json.dump(self.skipped_solutions, f, ensure_ascii=False, indent=4)
        with open(self.skipped_notifications_file, 'w', encoding='utf-8') as f:
            logger.info(f'Skipped notifications saved to {self.skipped_notifications_file}')
            json.dump(self.skipped_notifications, f, ensure_ascii=False, indent=4)

    def set_stat(self, item: Solution | Like, total_notifications: int = None):
        """Статистика. Отслеживаем лайки и скипы текущей сессии"""
        user_id, user_name, like_from, like_to = item.get_statistic_info()
        logger.debug(f'Processing {user_id}, {user_name}, {like_from}, {like_to}')
        if isinstance(item, Like) and not item.is_good:
            self.skipped_notifications.append({
                'user_id': user_id,
                'user_name': user_name,
                'url': item.what_was_liked_url,
                'reason': 'Not a solution or is a comment'
            })
        elif isinstance(item, Solution) and item.voted:  # Исключаем собственные решения
            self.skipped_solutions.append({
                'user_id': item.user_id,
                'user_name': item.user_name,
                'url': item.sol.get_attribute('data-url') if item.sol.get_attribute('data-url') else item.sol.get_attribute('href'),  # Точный URL решения
                'reason': 'Already voted'
            })
            # Ограничиваем количество скипов текущей сессией
            if total_notifications and len(self.skipped_solutions) > total_notifications:
                self.skipped_solutions.pop(0)  # Удаляем самый старый скип, если превышен лимит
        else:
            data = self.stat_data.get(user_id, {'names': [], 'likes_from': 0, 'likes_to': 0})
            if user_name not in data['names']:
                data['names'].append(user_name)
            data['likes_from'] += like_from
            data['likes_to'] += like_to
            self.stat_data[user_id] = data

if __name__ == '__main__':
    stat = Statistics()
    stat.set_stat(Like(None))  # Пример
    stat.dump_data()