"""
Обработчик команд: голосовой цикл (process_commands), маршрутизация команды к нужному
действию (route_command) и обработка текстового ввода из интерфейса (handle_typed_command).
"""
import os
import re
import time
import threading
import webbrowser
import urllib.parse
import pyautogui

from config import BOT_NAME_LOWER, COLOR_MUTED, COLOR_BLUE
from runtime_state import update_gui_status, update_reactor_color, voice_output_state, append_chat_log
from tts import speak
from speech import listen, calibrate_microphone
from helpers import start_timer, call_ultron, open_app
import memory_store
from notes import save_note, search_notes, list_recent_notes
from presentations import create_presentation, is_presentation_request, PRESENTATION_TRIGGERS
from ai import (
    ask_ai, is_study_question, is_problem_question, is_search_request, answer_with_search,
    is_homework_check_request, check_homework, HOMEWORK_CHECK_TRIGGERS,
)
import quiz


def process_commands():
    time.sleep(1)
    calibrate_microphone()
    speak("Системы онлайн. Я вас слушаю, сэр.")

    while True:
        query = listen()
        if not query:
            update_gui_status("🔵 РЕЖИМ ОЖИДАНИЯ", color=COLOR_MUTED)
            update_reactor_color(COLOR_BLUE)
            continue

        # --- WAKE WORD: реагируем только если явно произнесено "Джарвис" ---
        if BOT_NAME_LOWER not in query and "jarvis" not in query:
            update_gui_status("🔵 ОЖИДАНИЕ КЛЮЧЕВОГО СЛОВА", color=COLOR_MUTED)
            update_reactor_color(COLOR_BLUE)
            continue

        clean_query = re.sub(rf"\b({BOT_NAME_LOWER}|jarvis)\b", "", query).strip()
        if not clean_query:
            clean_query = query

        route_command(clean_query)


def route_command(clean_query):
    """Определяет и выполняет нужное действие по тексту команды. Используется и голосовым
    циклом, и текстовым вводом в интерфейсе — логика общая."""
    # --- ВИКТОРИНА АКТИВНА: следующая фраза — это ответ на вопрос, а не новая команда ---
    if quiz.current_quiz_question:
        quiz.submit_quiz_answer(clean_query)
        return

    # --- Управление окнами и медиа ---
    if any(w in clean_query for w in ["пауза", "стоп музыка", "останови"]):
        pyautogui.press("space")
        speak("Готово, сэр.")
    elif any(w in clean_query for w in ["продолжи", "играй"]):
        pyautogui.press("space")
        speak("Продолжаю.")
    elif any(w in clean_query for w in ["следующий", "вперед"]):
        pyautogui.hotkey("shift", "n")
        speak("Переключаю.")
    elif "сверни все" in clean_query or "сверни окна" in clean_query:
        pyautogui.hotkey("win", "d")
        speak("Сворачиваю окна.")
    elif "скриншот" in clean_query or "сделай снимок" in clean_query:
        pyautogui.hotkey("win", "prtsc")
        speak("Скриншот сделан.")

    # --- Таймеры ---
    elif "напомни" in clean_query or "таймер" in clean_query:
        digits = re.findall(r"\d+", clean_query)
        seconds = int(digits[0]) * 60 if digits else 60
        task = clean_query.replace("напомни", "").replace("таймер", "").strip() or "Задание"
        speak(f"Принято. Напомню через {seconds // 60} мин.")
        threading.Thread(target=start_timer, args=(seconds, task), daemon=True).start()

    # --- Запуск программ ---
    elif "capcut" in clean_query:
        open_app("capcut", "start capcut")
    elif "unity" in clean_query:
        open_app("unity", "start unity")
    elif "shotcut" in clean_query:
        open_app("shotcut", "start shotcut")
    elif "pubg" in clean_query:
        open_app("pubg", "start steam://rungame/578080")

    # --- Кино и Музыка ---
    elif any(
        w in clean_query
        for w in ["фильм", "кино", "сериал", "музыку", "песню", "трек", "поставь", "включи", "слушать"]
    ):
        words_to_remove = [
            BOT_NAME_LOWER, "jarvis", "открой", "включи", "поставь",
            "найди", "слушать", "хочу", "музыку", "песню", "трек", "послушать",
            "фильм", "кино", "сериал",
        ]
        search_text = clean_query
        for word in words_to_remove:
            search_text = re.sub(rf"\b{re.escape(word)}\b", "", search_text, flags=re.IGNORECASE)
        search_text = re.sub(r"\s+", " ", search_text).strip()

        if search_text:
            speak(f"Ищу и включаю: {search_text}")
            encoded_query = urllib.parse.quote(search_text)
            webbrowser.open(
                f"https://www.youtube.com/results?search_query={encoded_query}&sp=EgIQAQ%253D%253D"
            )
        else:
            speak("Открываю YouTube")
            webbrowser.open("https://youtube.com")

    # --- Питание ПК ---
    elif "выключи компьютер" in clean_query:
        speak("Завершаю работу Windows.")

        os.system("shutdown /s /t 5")
    elif "перезагрузи компьютер" in clean_query:
        speak("Перезагружаю систему.")

        os.system("shutdown /r /t 5")

    # --- Связь ---
    elif any(w in clean_query for w in ["позвони альтрону", "свяжи с альтроном"]):
        call_ultron()
    elif any(w in clean_query for w in ["выключись", "пока", "выход", "закройся"]):
        speak("Отключаю системы. До свидания, сэр.")

        os._exit(0)

    # --- НОВАЯ ТЕМА / СБРОС ПАМЯТИ ---
    elif "новая тема" in clean_query or "забудь тему" in clean_query:
        memory_store.study_history.clear()
        memory_store.problem_history.clear()
        memory_store.save_memory()
        speak("Хорошо, начинаем с чистого листа, сэр.")

    # --- ПОИСК В ИНТЕРНЕТЕ ---
    elif is_search_request(clean_query):
        answer = answer_with_search(clean_query)
        speak(answer)

    # --- СОХРАНЕНИЕ КОНСПЕКТА ---
    elif "сохрани это" in clean_query or "сохрани конспект" in clean_query:
        if memory_store.last_saved_answer:
            save_note(memory_store.last_saved_question, memory_store.last_saved_answer)
            speak("Конспект сохранён, сэр.")
        else:
            speak("Пока нечего сохранять, сэр. Сначала задайте учебный вопрос.")

    # --- СПИСОК ПОСЛЕДНИХ КОНСПЕКТОВ ---
    elif "мои конспекты" in clean_query or "покажи конспекты" in clean_query:
        recent = list_recent_notes(5)
        if recent:
            titles = "; ".join(title for _, title in recent)
            speak(f"Вот ваши последние конспекты: {titles}")
        else:
            speak("Пока нет сохранённых конспектов, сэр.")

    # --- ПОИСК ПО КОНСПЕКТАМ ---
    elif "найди конспект" in clean_query or "что я спрашивал про" in clean_query:
        search_term = clean_query
        for trigger in ["найди конспект про", "найди конспект", "что я спрашивал про"]:
            search_term = search_term.replace(trigger, "")
        search_term = search_term.strip()
        if not search_term:
            speak("Уточните, что именно искать, сэр.")
        else:
            matches = search_notes(search_term)
            if matches:
                titles = "; ".join(title for _, title in matches)
                speak(f"Нашёл {len(matches)} конспект(ов) про {search_term}: {titles}")
            else:
                speak(f"Не нашёл конспектов про {search_term}, сэр.")

    # --- ПРОВЕРКА ДОМАШНЕГО ЗАДАНИЯ ---
    elif is_homework_check_request(clean_query):
        user_text = clean_query
        for trigger in HOMEWORK_CHECK_TRIGGERS:
            user_text = user_text.replace(trigger, "")
        user_text = user_text.strip()
        if not user_text:
            speak("Расскажите, что за задача и как вы её решили, сэр.")
        else:
            speak("Проверяю, сэр. Секунду...")
            feedback = check_homework(user_text)
            speak(feedback)

    # --- ВИКТОРИНА: НАЧАТЬ ---
    elif quiz.is_quiz_start_request(clean_query):
        topic = clean_query
        for trigger in quiz.QUIZ_START_TRIGGERS:
            topic = topic.replace(trigger + " по", "").replace(trigger, "")
        topic = topic.strip()
        quiz.start_quiz(topic if topic else None)

    # --- СОЗДАНИЕ ПРЕЗЕНТАЦИИ ---
    elif is_presentation_request(clean_query):
        topic = clean_query
        for trigger in PRESENTATION_TRIGGERS:
            topic = topic.replace(trigger, "")
        topic = topic.strip() or "без темы"
        create_presentation(topic)

    # --- РЕШЕНИЕ ЗАДАЧ (экономика, расчёты, формулы) ---
    elif is_problem_question(clean_query):
        speak("Решаю, сэр. Секунду...")
        answer = ask_ai(clean_query, mode="problem")
        speak(answer)

    # --- ОБЪЯСНЕНИЕ ТЕМ (репетитор) ---
    elif is_study_question(clean_query):
        speak("Секунду, разбираюсь...")
        answer = ask_ai(clean_query, mode="study")
        speak(answer)

    # --- AI Ответ (обычный режим) ---
    else:
        answer = ask_ai(clean_query, mode="chat")
        speak(answer)


def handle_typed_command(text):
    """Обрабатывает текст, введённый вручную в интерфейсе — так же, как голосовую команду,
    но без требования произносить wake word и без озвучки ответа (только текст в журнале)."""
    text = text.strip()
    if not text:
        return
    append_chat_log(f"Вы (текст): {text}\n")
    clean_query = re.sub(rf"\b({BOT_NAME_LOWER}|jarvis)\b", "", text.lower()).strip()
    if not clean_query:
        clean_query = text.lower()

    def run():
        voice_output_state.enabled = False
        route_command(clean_query)

    threading.Thread(target=run, daemon=True).start()