# Файл: class_statistics.py
# Описание: Добавлены счётчики для лайков комментариев
import json
from pathlib import Path
from class_logger import get_logger

logger = get_logger('class_statistics')

class Statistics:
    def __init__(self):
        self.new_likes = 0
        self.old_likes = 0
        self.skipped_solutions = []
        self.load_data()

    def load_data(self):
        stats_file = Path("like_stats.json")
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.new_likes = data.get('new_likes', 0)
                    self.old_likes = data.get('old_likes', 0)
                    self.skipped_solutions = data.get('skipped_solutions', [])
                    self.comment_likes = data.get('comment_likes', 0)  # Новый счётчик
            except Exception as e:
                logger.error(f"Failed to load stats from {stats_file}: {str(e)}")

    def increment_solution_likes(self):
        self.new_likes += 1

    def increment_comment_likes(self):
        self.comment_likes += 1

    def set_stat(self, like):
        # Здесь можно добавить логику проверки, был ли лайк ранее
        pass  # Пока оставим как есть, можно доработать позже

    def dump_data(self):
        data = {
            'new_likes': self.new_likes,
            'old_likes': self.old_likes,
            'comment_likes': getattr(self, 'comment_likes', 0),  # Новый ключ
            'skipped_solutions': self.skipped_solutions
        }
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        stats_file = log_dir / "like_stats.json"
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved stats to {stats_file}")
        except Exception as e:
            logger.error(f"Failed to save stats to {stats_file}: {str(e)}")

if __name__ == '__main__':
    stat = Statistics()
    stat.increment_solution_likes()
    stat.increment_comment_likes()
    stat.dump_data()