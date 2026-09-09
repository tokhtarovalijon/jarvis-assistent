"""
Вспомогательные функции: таймеры/напоминания, связь через Telegram, запуск внешних программ.
"""
import os
import time

from config import bot, TELEGRAM_CHAT_ID, APP_PATHS
from tts import speak


def start_timer(seconds, message):
    time.sleep(seconds)
    speak(f"Сэр, время вышло! Напоминаю: {message}")


def call_ultron():
    speak("Устанавливаю защищенное соединение с Альтроном...")
    if bot:
        try:
            bot.send_message(TELEGRAM_CHAT_ID, "⚠️ Запрос на связь от сэра! Джарвис на линии.")
            speak("Сигнал передан. Альтрон уведомлен.")
        except Exception as e:
            print(f"[Telegram ошибка] {e}")
            speak("Ошибка передачи сигнала в Telegram.")
    else:
        speak("Служба Telegram не настроена.")


def open_app(app_name, default_command):
    speak(f"Запускаю {app_name}, сэр.")
    try:
        path = APP_PATHS.get(app_name, "")
        if path and os.path.exists(path):
            os.startfile(path)
        else:
            os.system(default_command)
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        speak(f"Не удалось запустить {app_name}.")
