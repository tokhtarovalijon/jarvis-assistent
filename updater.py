"""
Автообновление: при старте программа проверяет GitHub-репозиторий на новую версию
и, если она есть, скачивает обновлённые файлы. Если GitHub не настроен (GITHUB_USER
не изменён), проверка тихо пропускается — программа просто запускается как обычно.

НАСТРОЙКА (см. инструкцию, которую прислал Джарвис):
1. Создайте публичный репозиторий на github.com
2. Загрузите туда ВСЕ .py файлы проекта + файл version.txt с текстом "1.0.0" внутри
3. Впишите ниже ваш логин GitHub и название репозитория
4. При каждом обновлении: меняете код, увеличиваете версию в version.txt на GitHub
   (например на "1.0.1"), загружаете обновлённые файлы — и все, у кого установлен
   Джарвис, получат уведомление при следующем запуске.
"""
import os
import requests

CURRENT_VERSION = "1.0.0"

# Замените на свои данные после настройки репозитория на GitHub
GITHUB_USER = "ваш_логин_github"
GITHUB_REPO = "jarvis-assistant"
GITHUB_BRANCH = "main"

FILES_TO_UPDATE = [
    "main.py", "config.py", "runtime_state.py", "tts.py", "helpers.py",
    "memory_store.py", "notes.py", "ai.py", "presentations.py", "speech.py",
    "commands.py", "gui.py", "quiz.py", "updater.py",
]
# ВАЖНО: secrets_local.py намеренно НЕ включён в этот список и никогда не должен
# в него попасть — он содержит ваши личные ключи API и не публикуется на GitHub.

RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"


def is_configured():
    return GITHUB_USER != "ваш_логин_github"


def check_for_update():
    """Возвращает номер новой версии (строку), если на GitHub версия отличается
    от текущей. Иначе возвращает None (обновлений нет или GitHub не настроен)."""
    if not is_configured():
        return None
    try:
        response = requests.get(f"{RAW_BASE}/version.txt", timeout=5)
        response.raise_for_status()
        remote_version = response.text.strip()
        if remote_version and remote_version != CURRENT_VERSION:
            return remote_version
    except Exception as e:
        print(f"[Автообновление] Не удалось проверить обновления: {e}")
    return None


def download_update():
    """Скачивает все файлы проекта с GitHub и перезаписывает локальные копии.
    Возвращает True, если всё прошло успешно."""
    for filename in FILES_TO_UPDATE:
        try:
            response = requests.get(f"{RAW_BASE}/{filename}", timeout=10)
            response.raise_for_status()
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"[Автообновление] Обновлён файл: {filename}")
        except Exception as e:
            print(f"[Автообновление] Ошибка обновления {filename}: {e}")
            return False
    return True
