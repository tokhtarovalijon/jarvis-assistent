"""
Общие настройки и цветовая палитра.
Этот модуль не зависит от других модулей проекта — его можно импортировать откуда угодно.

Реальные ключи API хранятся ОТДЕЛЬНО, в secrets_local.py — этот файл нельзя загружать
на GitHub. Здесь только безопасная для публикации логика.
"""
import os
import sys
from groq import Groq
import telebot
import customtkinter as ctk

# --- 0. НАСТРОЙКИ И ПУТИ К ПРОГРАММАМ ---
# При обычном запуске (python main.py) рабочая папка — там, где лежит main.py.
# При запуске собранного .exe (PyInstaller) — рабочая папка рядом с самим .exe,
# а НЕ во временной папке распаковки (иначе конспекты/презентации/память терялись
# бы после каждого закрытия программы).
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    from secrets_local import GROQ_API_KEY, PEXELS_API_KEY
except ImportError:
    print(
        "ВНИМАНИЕ: файл secrets_local.py не найден. Создайте его рядом с main.py "
        "и впишите туда GROQ_API_KEY и PEXELS_API_KEY."
    )
    GROQ_API_KEY = None
    PEXELS_API_KEY = None

if not GROQ_API_KEY or GROQ_API_KEY.startswith("gsk_ваш"):
    print("ВНИМАНИЕ: GROQ_API_KEY не задан. ИИ-ответы работать не будут.")
    GROQ_API_KEY = None
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

if not PEXELS_API_KEY or PEXELS_API_KEY.startswith("ваш_ключ"):
    print("ВНИМАНИЕ: PEXELS_API_KEY не задан. Презентации будут без фото-фонов.")
    PEXELS_API_KEY = None

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

BOT_NAME = "Джарвис"
BOT_NAME_LOWER = "джарвис"

# --- HUD ЦВЕТОВАЯ СХЕМА (стиль Iron Man / J.A.R.V.I.S.) ---
COLOR_BG = "#1A1D21"        # фон окна — нейтральный тёмно-серый (как на референсе)
COLOR_PANEL = "#22262B"     # фон панелей
COLOR_PANEL_DARK = "#15171A"
COLOR_BORDER = "#4DD9E8"    # бирюзово-голубая окантовка (вместо оранжевой)
COLOR_BLUE = "#3AB8C7"      # ожидание / ambient — приглушённая бирюза
COLOR_CYAN = "#7FEFFA"      # слушаю — яркий голубой
COLOR_ORANGE = "#F2F2F0"    # обрабатываю — серебристо-белый (вместо оранжевого)
COLOR_SPEAK = "#8FF5FF"     # говорю — яркое голубое свечение
COLOR_MUTED = "#5A6570"     # приглушённый текст

# Укажите реальные пути к .exe, если хотите запускать программы напрямую.
# Если путь пустой — сработает default_command (например, "start capcut").
APP_PATHS = {
    "capcut": r"",
    "unity": r"",
    "shotcut": r"",
    "pubg": r"",
}

# --- КРАСИВЫЙ ИНТЕРФЕЙС (глобальная тема customtkinter) ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
