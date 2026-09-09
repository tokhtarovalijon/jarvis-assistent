"""
Общие настройки и цветовая палитра.
Этот модуль не зависит от других модулей проекта — его можно импортировать откуда угодно.

Реальные ключи API хранятся ОТДЕЛЬНО, в secrets_local.py — этот файл нельзя загружать
на GitHub. Здесь только безопасная для публикации логика.
"""
import os
from groq import Groq
import telebot
import customtkinter as ctk

# --- 0. НАСТРОЙКИ И ПУТИ К ПРОГРАММАМ ---
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
COLOR_BG = "#04070E"        # фон окна — почти чёрный тёмно-синий
COLOR_PANEL = "#0A1424"     # фон панелей
COLOR_PANEL_DARK = "#060D18"
COLOR_BORDER = "#FF8C00"    # оранжевая HUD-окантовка
COLOR_BLUE = "#2FA8FF"      # ожидание / ambient — арк-реактор синий
COLOR_CYAN = "#00E5FF"      # слушаю
COLOR_ORANGE = "#FF8C00"    # обрабатываю
COLOR_SPEAK = "#FF4B2B"     # говорю — активный оранжево-красный
COLOR_MUTED = "#4A6685"     # приглушённый текст

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