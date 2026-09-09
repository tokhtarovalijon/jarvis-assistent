"""
"Мост" между потоками и GUI: здесь хранится ссылка на активное окно приложения (app_instance)
и потокобезопасные флаги (прерывание речи, отключение голоса для текстового ввода).

Этот модуль — "лист" в дереве импортов: он ничего не импортирует из других модулей проекта,
поэтому его может безопасно импортировать любой другой файл без риска циклического импорта.
"""
import threading

# --- ССЫЛКА НА ОКНО ПРИЛОЖЕНИЯ (устанавливается в main.py при старте) ---
app_instance = None


def update_reactor_color(color):
    if app_instance:
        app_instance.update_reactor_color(color)


def update_gui_status(text, color="#FFFFFF"):
    if app_instance:
        app_instance.update_gui_status(text, color)


def append_chat_log(text):
    if app_instance:
        app_instance.append_chat_log(text)


# --- ПРЕРЫВАНИЕ РЕЧИ КЛАВИШЕЙ Esc ---
stop_speech_event = threading.Event()

# --- ОТКЛЮЧЕНИЕ ГОЛОСА ДЛЯ ТЕКСТОВЫХ КОМАНД (только в потоке, который их обрабатывает) ---
voice_output_state = threading.local()


def is_voice_output_enabled():
    return getattr(voice_output_state, "enabled", True)
