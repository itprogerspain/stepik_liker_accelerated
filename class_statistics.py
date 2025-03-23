from class_logger import get_logger
import json
from pathlib import Path
from class_like import Like
from class_solution import Solution
from datetime import datetime

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
        self.current_session_likes = []
        self.session_file = 'current_session_likes.json'  # Фиксированное имя файла
        self.__load_data()

    def __load_data(self):
        # Оставляем только инициализацию current_session_likes.json, остальные файлы не трогаем
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump([], f)

    def dump_data(self):
        """Сохранение только current_session_likes.json"""
        with open(self.session_file, 'w', encoding='utf-8') as f:
            logger.info(f'Current session likes saved to {self.session_file}')
            json.dump(self.current_session_likes, f, ensure_ascii=False, indent=4)

    def set_stat(self, item: Solution | Like, total_notifications: int = None, failed: bool = False):
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
            # Устанавливаем статус "pending" для уведомлений, которые не прошли проверку is_good
            self.current_session_likes.append({
                'user_id': user_id,
                'user_name': user_name,
                'url': item.what_was_liked_url,
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            })
            logger.info(f"Added like from {user_name} (ID: {user_id}) to current session with status 'pending'")
        elif isinstance(item, Solution) and item.voted:  # Исключаем собственные решения
            self.skipped_solutions.append({
                'user_id': item.user_id,
                'user_name': item.user_name,
                'url': item.sol.get_attribute('data-url') if item.sol.get_attribute('data-url') else item.sol.get_attribute('href'),
                'reason': 'Already voted'
            })
            # Ограничиваем количество скипов текущей сессией
            if total_notifications and len(self.skipped_solutions) > total_notifications:
                self.skipped_solutions.pop(0)  # Удаляем самый старый скип, если превышен лимит
        elif isinstance(item, Like) and item.is_good:
            # Для уведомлений, которые прошли проверку is_good, добавляем запись с временным статусом
            self.current_session_likes.append({
                'user_id': user_id,
                'user_name': user_name,
                'url': item.what_was_liked_url,
                'timestamp': datetime.now().isoformat(),
                'status': 'awaiting'  # Временный статус, будет обновлён позже
            })
            logger.info(f"Added like from {user_name} (ID: {user_id}) to current session with initial status 'awaiting'")
        else:
            data = self.stat_data.get(user_id, {'names': [], 'likes_from': 0, 'likes_to': 0})
            if user_name not in data['names']:
                data['names'].append(user_name)
            data['likes_from'] += like_from
            data['likes_to'] += like_to
            self.stat_data[user_id] = data

    def update_like_status(self, like: Like, status: str):
        """Обновляет статус и время обработки лайка после попытки поставить лайк"""
        for entry in self.current_session_likes:
            if entry['user_id'] == like.user_id and entry['url'] == like.what_was_liked_url:
                entry['status'] = status
                entry['timestamp'] = datetime.now().isoformat()  # Обновляем время на момент обработки
                logger.info(f"Updated like from {like.user_name} (ID: {like.user_id}) to status {entry['status']} at {entry['timestamp']}")
                break

if __name__ == '__main__':
    stat = Statistics()
    stat.set_stat(Like(None))  # Пример
    stat.dump_data()