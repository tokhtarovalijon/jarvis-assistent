"""
Автообновление. Работает по-разному в зависимости от того, как запущен Джарвис:

1) Запуск через "python main.py" (обычный режим разработки):
   Проверяет version.txt в репозитории на GitHub, и если версия отличается —
   скачивает обновлённые .py-файлы и перезаписывает локальные копии.

2) Запуск через собранный Jarvis.exe (PyInstaller):
   Проверяет последний GitHub Release репозитория. Если там версия (тег) отличается —
   скачивает НОВЫЙ .exe из вложений релиза, сам себя заменяет на диске и перезапускается.
   Работает именно так, потому что готовый .exe не может "подхватить" изменения в
   .py-файлах — все они уже скомпилированы внутрь него на момент сборки.

Если GitHub не настроен (GITHUB_USER не изменён) — обе проверки тихо пропускаются,
программа просто запускается как обычно.

НАСТРОЙКА:
1. Создайте публичный репозиторий на github.com, впишите логин/название ниже.
2. Для режима "python main.py": загрузите в репозиторий все .py файлы + version.txt
   с текущей версией внутри (например "1.0.0").
3. Для режима .exe: соберите Jarvis.exe (см. инструкцию Джарвиса), затем на GitHub
   откройте вкладку "Releases" -> "Create a new release" -> Tag: например "1.0.1"
   -> прикрепите файл Jarvis.exe как вложение -> Publish release.
4. При каждом обновлении .exe: увеличивайте CURRENT_VERSION в этом файле ДО сборки
   новой версии, соберите .exe, опубликуйте новый Release с тем же номером версии
   в теге и новым Jarvis.exe как вложением.
"""
import os
import sys
import subprocess
import requests

CURRENT_VERSION = "1.0.1"

# Замените на свои данные после настройки репозитория на GitHub
GITHUB_USER = "tokhtarovalijon"
GITHUB_REPO = "jarvis-assistent"
GITHUB_BRANCH = "main"

EXE_NAME = "Jarvis.exe"

FILES_TO_UPDATE = [
    "main.py", "config.py", "runtime_state.py", "tts.py", "helpers.py",
    "memory_store.py", "notes.py", "ai.py", "presentations.py", "speech.py",
    "commands.py", "gui.py", "quiz.py", "updater.py", "settings.py", "stats.py",
    "study_schedule.py", "knowledge_base.py",
]
# ВАЖНО: secrets_local.py намеренно НЕ включён в этот список и никогда не должен
# в него попасть — он содержит ваши личные ключи API и не публикуется на GitHub.

RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"


def is_configured():
    return GITHUB_USER != "ваш_логин_github"


def is_frozen():
    """True, если это собранный .exe (PyInstaller), False - если обычный python main.py."""
    return getattr(sys, "frozen", False)


# --- РЕЖИМ 1: ОБНОВЛЕНИЕ ИСХОДНОГО КОДА (python main.py) ---

def check_for_update():
    """Возвращает номер новой версии (строку), если version.txt на GitHub отличается
    от текущей. Иначе None (обновлений нет или GitHub не настроен)."""
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
    """Скачивает все .py-файлы проекта с GitHub и перезаписывает локальные копии."""
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


# --- РЕЖИМ 2: САМООБНОВЛЕНИЕ СОБРАННОГО .exe (GitHub Releases) ---

def check_for_exe_update():
    """Возвращает (версия, ссылка_на_скачивание) если в GitHub Releases есть версия
    новее текущей и там прикреплён Jarvis.exe. Иначе None."""
    if not is_configured():
        return None
    try:
        response = requests.get(RELEASES_API, timeout=5)
        response.raise_for_status()
        data = response.json()
        latest_tag = data.get("tag_name", "").lstrip("v").strip()
        if not latest_tag or latest_tag == CURRENT_VERSION:
            return None
        for asset in data.get("assets", []):
            if asset.get("name") == EXE_NAME:
                return latest_tag, asset.get("browser_download_url")
    except Exception as e:
        print(f"[Автообновление] Не удалось проверить обновления .exe: {e}")
    return None


def download_and_apply_exe_update(download_url):
    """Скачивает новый .exe и запускает скрипт самозамены (текущий .exe завершится
    сразу после вызова этой функции). Возвращает True, если скачивание прошло успешно."""
    try:
        current_exe = sys.executable
        exe_dir = os.path.dirname(current_exe)
        new_exe_path = os.path.join(exe_dir, "Jarvis_new.exe")

        response = requests.get(download_url, timeout=120, stream=True)
        response.raise_for_status()
        with open(new_exe_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        bat_path = os.path.join(exe_dir, "_update_jarvis.bat")
        bat_content = (
            "@echo off\r\n"
            "timeout /t 2 /nobreak > nul\r\n"
            f'taskkill /IM "{os.path.basename(current_exe)}" /F > nul 2>&1\r\n'
            "timeout /t 1 /nobreak > nul\r\n"
            f'del "{current_exe}"\r\n'
            f'move /Y "{new_exe_path}" "{current_exe}"\r\n'
            f'start "" "{current_exe}"\r\n'
            "del \"%~f0\"\r\n"
        )
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)

        subprocess.Popen(
            ["cmd", "/c", bat_path],
            creationflags=subprocess.CREATE_NO_WINDOW,
            close_fds=True,
        )
        return True
    except Exception as e:
        print(f"[Автообновление] Ошибка применения обновления .exe: {e}")
        return False