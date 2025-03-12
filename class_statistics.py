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
        # Инициализация like_stats.json
        if not Path(self.stat_file_name).exists():
            with open(self.stat_file_name, 'w', encoding='utf-8') as f:
                json.dump({}, f)
        else:
            with open(self.stat_file_name, encoding='utf-8') as f:
                self.stat_data = json.load(f)

        # Инициализация skipped_solutions.json (перезаписываем)
        with open(self.skipped_solutions_file, 'w', encoding='utf-8') as f:
            json.dump([], f)

        # Инициализация skipped_notifications.json (перезаписываем)
        with open(self.skipped_notifications_file, 'w', encoding='utf-8') as f:
            json.dump([], f)

    def dump_data(self):
        """Сохранение всех файлов статистики"""
        with open(self.stat_file_name, 'w', encoding='utf-8') as f:
            logger.info(f'Stat data saved to {self.stat_file_name}')
            json.dump(self.stat_data, f, ensure_ascii=False, indent=4)
        with open(self.skipped_solutions_file, 'w', encoding='utf-8') as f:
            logger.info(f'Skipped solutions saved to {self.skipped_solutions_file}')
            json.dump(self.skipped_solutions, f, ensure_ascii=False, indent=4)
        with open(self.skipped_notifications_file, 'w', encoding='utf-8') as f:
            logger.info(f'Skipped notifications saved to {self.skipped_notifications_file}')
            json.dump(self.skipped_notifications, f, ensure_ascii=False, indent=4)

    def set_stat(self, item: Solution | Like):
        """Статистика. Отслеживаем лайки и скипы"""
        user_id, user_name, like_from, like_to = item.get_statistic_info()
        logger.debug(f'Processing {user_id}, {user_name}, {like_from}, {like_to}')
        if isinstance(item, Like) and not item.is_good:
            self.skipped_notifications.append({
                'user_id': user_id,
                'user_name': user_name,
                'url': item.what_was_liked_url,
                'reason': 'Not a solution or is a comment'
            })
        elif isinstance(item, Solution) and (item.user_id == item.STEPIK_SELF_ID or item.voted):
            self.skipped_solutions.append({
                'user_id': item.user_id,
                'user_name': item.user_name,
                'url': item.sol.get_attribute('href') if hasattr(item, 'sol') else 'N/A',
                'reason': 'Own solution' if item.user_id == item.STEPIK_SELF_ID else 'Already voted'
            })
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