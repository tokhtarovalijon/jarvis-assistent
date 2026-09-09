"""
Сохранение, поиск и просмотр списка конспектов учебных ответов (markdown-файлы).
"""
import os
from datetime import datetime

NOTES_DIR = "конспекты"
os.makedirs(NOTES_DIR, exist_ok=True)


def save_note(question, answer):
    if not answer:
        return None
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(NOTES_DIR, f"конспект_{timestamp}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {question}\n\n")
        f.write(f"*Сохранено: {datetime.now().strftime('%d.%m.%Y %H:%M')}*\n\n")
        f.write(answer)
    return filename


def _note_title(filepath):
    """Возвращает заголовок (первую строку без '# ') сохранённого конспекта."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            first_line = f.readline()
        return first_line.lstrip("#").strip() or "Без темы"
    except Exception:
        return "Без темы"


def list_recent_notes(limit=5):
    """Возвращает список последних N конспектов: [(имя_файла, заголовок), ...]."""
    if not os.path.isdir(NOTES_DIR):
        return []
    files = [f for f in os.listdir(NOTES_DIR) if f.endswith(".md")]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(NOTES_DIR, f)), reverse=True)
    return [(f, _note_title(os.path.join(NOTES_DIR, f))) for f in files[:limit]]


def search_notes(query, limit=5):
    """Ищет конспекты, содержащие query (без учёта регистра) в заголовке или тексте.
    Возвращает список: [(имя_файла, заголовок), ...]."""
    if not query or not os.path.isdir(NOTES_DIR):
        return []
    query_lower = query.lower()
    matches = []
    files = [f for f in os.listdir(NOTES_DIR) if f.endswith(".md")]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(NOTES_DIR, f)), reverse=True)
    for filename in files:
        filepath = os.path.join(NOTES_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue
        if query_lower in content.lower():
            matches.append((filename, _note_title(filepath)))
        if len(matches) >= limit:
            break
    return matches