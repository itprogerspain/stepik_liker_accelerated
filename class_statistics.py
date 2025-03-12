# Файл: class_statistics.py
# Описание: Добавлена статистика скипнутых решений с перезаписью
import json
import datetime
from pathlib import Path
from class_logger import get_logger
from class_like import Like
from class_solution import Solution

logger = get_logger('class_statistics')

class Statistics:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, stat_file_name='like_stats.json', skipped_file_name='skipped_solutions.json'):
        self.stat_file_name = stat_file_name
        self.skipped_file_name = skipped_file_name
        self.stat_data = {}
        self.skipped_solutions = []  # Список скипнутых решений
        self.__load_data()

    def __load_data(self):
        if not Path(self.stat_file_name).exists():
            with open(self.stat_file_name, 'w') as f:
                json.dump({}, f)
        else:
            with open(self.stat_file_name, encoding='utf-8') as f:
                self.stat_data = json.load(f)

        # Перезаписываем skipped_solutions.json как пустой список
        with open(self.skipped_file_name, 'w') as f:
            json.dump([], f)

    def dump_data(self):
        with open(self.stat_file_name, 'w', encoding='utf-8') as f:
            logger.info(f'Stat data saved to {self.stat_file_name}')
            json.dump(self.stat_data, f, ensure_ascii=False, indent=4)
        with open(self.skipped_file_name, 'w', encoding='utf-8') as f:
            logger.info(f'Skipped solutions saved to {self.skipped_file_name}')
            json.dump(self.skipped_solutions, f, ensure_ascii=False, indent=4)

    def set_stat(self, item: Solution | Like):
        new_values = lambda: {'names': [], 'likes_from': 0, 'likes_to': 0}
        user_id, user_name, like_from, like_to = item.get_statistic_info()
        logger.debug(f'{user_id}, {user_name}, {like_from}, {like_to}')
        data = self.stat_data.get(user_id, new_values())
        if user_name not in data['names']:
            data['names'].append(user_name)
        data['likes_from'] += like_from
        data['likes_to'] += like_to
        self.stat_data[user_id] = data

    def mark_skipped_solution(self, solution_url: str, user_id: str, user_name: str, reason: str):
        skipped_entry = {
            'solution_url': solution_url,
            'user_id': user_id,
            'user_name': user_name,
            'reason': reason,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.skipped_solutions.append(skipped_entry)
        logger.warning(f'Skipped solution: {solution_url}, ID={user_id}, Name={user_name}, Reason={reason}')

if __name__ == '__main__':
    ...