"""
Статистика активности: сколько конспектов сохранено, презентаций создано,
викторин пройдено, домашних заданий проверено.
"""
import os
import json

from notes import NOTES_DIR
from presentations import PRESENTATIONS_DIR

STATS_FILE = "статистика.json"


def _load_stats():
    if not os.path.exists(STATS_FILE):
        return {"quizzes_taken": 0, "homework_checks": 0}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"quizzes_taken": 0, "homework_checks": 0}


def _save_stats(stats):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Ошибка сохранения статистики] {e}")


def increment(key):
    stats = _load_stats()
    stats[key] = stats.get(key, 0) + 1
    _save_stats(stats)


def get_summary():
    stats = _load_stats()
    notes_count = 0
    if os.path.isdir(NOTES_DIR):
        notes_count = len([f for f in os.listdir(NOTES_DIR) if f.endswith((".md", ".docx"))])

    presentations_count = 0
    if os.path.isdir(PRESENTATIONS_DIR):
        presentations_count = len([f for f in os.listdir(PRESENTATIONS_DIR) if f.endswith(".pptx")])

    quizzes = stats.get("quizzes_taken", 0)
    homework = stats.get("homework_checks", 0)

    return (
        f"Конспектов сохранено: {notes_count}. Презентаций создано: {presentations_count}. "
        f"Викторин пройдено: {quizzes}. Домашних заданий проверено: {homework}."
    )