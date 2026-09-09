"""
Распознавание речи через микрофон (Google Speech Recognition).
"""
import speech_recognition as sr

from config import COLOR_CYAN, COLOR_ORANGE, COLOR_BLUE
from runtime_state import update_gui_status, update_reactor_color, append_chat_log

recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.8
recognizer.non_speaking_duration = 0.8
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True


def calibrate_microphone():
    """Калибрует уровень фонового шума ОДИН РАЗ при старте программы, а не на каждой
    голосовой команде — раньше это добавляло лишние 0.5с задержки к каждому запросу."""
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"[Микрофон] Калибровка завершена, порог шума: {recognizer.energy_threshold:.0f}")
    except Exception as e:
        print(f"[Ошибка калибровки микрофона] {e}")


def listen():
    try:
        with sr.Microphone() as source:
            update_gui_status("🎤 СЛУШАЮ...", color=COLOR_CYAN)
            update_reactor_color(COLOR_CYAN)
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=15)

            update_gui_status("⚡ ОБРАБОТКА СИГНАЛА...", color=COLOR_ORANGE)
            update_reactor_color(COLOR_ORANGE)
            query = recognizer.recognize_google(audio, language="ru-RU")
            print(f"Вы: {query}")
            append_chat_log(f"Вы: {query}\n")
            return query.lower()
    except sr.WaitTimeoutError:
        pass
    except sr.UnknownValueError:
        pass
    except Exception as e:
        print(f"[Ошибка распознавания] {e}")
    update_reactor_color(COLOR_BLUE)
    return ""
