"""
Режим викторины: Джарвис составляет вопрос по сохранённым конспектам (или по заданной теме)
и проверяет устный ответ — быстрая подготовка к экзамену.

Пока задан вопрос (current_quiz_question не пустой), route_command в commands.py направляет
СЛЕДУЮЩУЮ фразу пользователя не в обычную маршрутизацию, а сразу в submit_quiz_answer().
"""
import os
import random

from config import client, BOT_NAME
from tts import speak
from notes import NOTES_DIR

QUIZ_START_TRIGGERS = [
    "начни викторину", "проверь меня", "задай вопрос", "устрой викторину",
]

# --- Состояние текущей викторины (один активный вопрос за раз) ---
current_quiz_question = None
current_quiz_answer = None


def is_quiz_start_request(text):
    return any(trigger in text for trigger in QUIZ_START_TRIGGERS)


def _load_random_note_content():
    """Берёт случайный сохранённый конспект и возвращает его текст (для темы вопроса)."""
    if not os.path.isdir(NOTES_DIR):
        return None
    files = [f for f in os.listdir(NOTES_DIR) if f.endswith(".md")]
    if not files:
        return None
    filename = random.choice(files)
    try:
        with open(os.path.join(NOTES_DIR, filename), "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _generate_quiz_question(source_text):
    """Просит ИИ составить один короткий вопрос с эталонным ответом по материалу."""
    if not client:
        return None, None
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Составь ОДИН короткий проверочный вопрос по экономике на основе "
                        "материала ниже, подходящий для устного ответа студента. Ответь "
                        "СТРОГО в формате:\nВОПРОС: <текст вопроса>\n"
                        "ОТВЕТ: <краткий эталонный ответ, 1-2 предложения>"
                    ),
                },
                {"role": "user", "content": source_text},
            ],
            temperature=0.6,
            max_tokens=300,
        )
        text = response.choices[0].message.content
        question, answer = "", ""
        for line in text.splitlines():
            line = line.strip()
            if line.upper().startswith("ВОПРОС:"):
                question = line.split(":", 1)[1].strip()
            elif line.upper().startswith("ОТВЕТ:"):
                answer = line.split(":", 1)[1].strip()
        return question or None, answer or None
    except Exception as e:
        print(f"[Ошибка генерации вопроса викторины] {e}")
        return None, None


def _evaluate_answer(question, reference_answer, user_answer):
    """Просит ИИ мягко оценить устный ответ студента по сравнению с эталонным."""
    if not client:
        return "Не могу проверить: ИИ-модуль не настроен, сэр."
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Ты — {BOT_NAME}, принимаешь устную проверку знаний по экономике. "
                        "Сравни ответ студента с эталонным. Если по сути верно — похвали "
                        "кратко. Если неверно или неполно — мягко поправь и объясни "
                        "правильный ответ. Отвечай 2-4 предложения, по-дружески."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Вопрос: {question}\nЭталонный ответ: {reference_answer}\n"
                        f"Ответ студента: {user_answer}"
                    ),
                },
            ],
            temperature=0.4,
            max_tokens=400,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[Ошибка проверки ответа викторины] {e}")
        return "Не удалось проверить ответ, сэр."


def start_quiz(topic=None):
    """Начинает викторину: по заданной теме, если она указана, иначе по случайному
    сохранённому конспекту."""
    global current_quiz_question, current_quiz_answer

    source = topic if topic else _load_random_note_content()
    if not source:
        speak(
            "У меня пока нет ни темы, ни сохранённых конспектов для викторины, сэр. "
            "Сначала что-нибудь изучите или назовите тему."
        )
        return

    question, answer = _generate_quiz_question(source)
    if not question:
        speak("Не удалось составить вопрос, сэр.")
        return

    current_quiz_question = question
    current_quiz_answer = answer
    speak(f"Вопрос: {question}")


def submit_quiz_answer(user_answer):
    """Проверяет устный ответ на текущий вопрос викторины и завершает раунд."""
    global current_quiz_question, current_quiz_answer

    if not current_quiz_question:
        speak("Сначала начните викторину, сэр.")
        return

    feedback = _evaluate_answer(current_quiz_question, current_quiz_answer, user_answer)
    speak(feedback)
    current_quiz_question = None
    current_quiz_answer = None
