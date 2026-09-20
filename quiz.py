"""
Режим викторины: Джарвис задаёт сессию минимум из 10 вопросов подряд по сохранённым
конспектам (или по заданной теме). После каждого устного ответа сразу говорит,
правильно или нет — если неправильно, объясняет верный ответ, — и переходит к
следующему вопросу автоматически, без повторной команды.

Пока сессия активна (current_quiz_question не пустой), route_command в commands.py
направляет СЛЕДУЮЩУЮ фразу пользователя не в обычную маршрутизацию, а сразу в
submit_quiz_answer().
"""
import os
import random

from config import client, BOT_NAME
from tts import speak
import stats
from notes import NOTES_DIR

QUIZ_START_TRIGGERS = [
    "начни викторину", "проверь меня", "задай вопрос", "устрой викторину",
]
QUIZ_STOP_TRIGGERS = [
    "стоп викторина", "хватит викторины", "останови викторину", "закончи викторину",
]

TARGET_QUESTIONS = 10

# --- Состояние текущей сессии викторины ---
current_quiz_question = None
current_quiz_answer = None
current_topic = None
questions_asked = 0
correct_count = 0


def is_quiz_start_request(text):
    return any(trigger in text for trigger in QUIZ_START_TRIGGERS)


def is_quiz_stop_request(text):
    return any(trigger in text for trigger in QUIZ_STOP_TRIGGERS)


def _load_random_note_content():
    """Берёт случайный сохранённый конспект и возвращает его текст (для темы вопросов)."""
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
                        "Составь ОДИН короткий проверочный вопрос по теме ниже, подходящий "
                        "для устного ответа студента. Не повторяй вопросы, которые могли уже "
                        "задаваться ранее по этой же теме — формулируй по-новому каждый раз. "
                        "Ответь СТРОГО в формате:\nВОПРОС: <текст вопроса>\n"
                        "ОТВЕТ: <краткий эталонный ответ, 1-2 предложения>"
                    ),
                },
                {"role": "user", "content": source_text},
            ],
            temperature=0.75,
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
    """Просит ИИ оценить устный ответ студента. Возвращает (верно: bool, пояснение: str)."""
    if not client:
        return False, "Не могу проверить: ИИ-модуль не настроен, сэр."
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Ты — {BOT_NAME}, принимаешь устную проверку знаний. Сравни ответ "
                        "студента с эталонным ПО СМЫСЛУ (не по дословному совпадению). "
                        "Ответь СТРОГО в этом формате:\n"
                        "ВЕРДИКТ: ВЕРНО или НЕВЕРНО\n"
                        "ОБЪЯСНЕНИЕ: <2-3 предложения. Если верно — коротко похвали. Если "
                        "неверно или неполно — скажи, что ответ неверный, и объясни "
                        "правильный ответ простыми словами.>"
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
            temperature=0.3,
            max_tokens=400,
        )
        text = response.choices[0].message.content
        verdict = ""
        explanation_parts = []
        capturing = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.upper().startswith("ВЕРДИКТ:"):
                verdict = stripped.split(":", 1)[1].strip().upper()
            elif stripped.upper().startswith("ОБЪЯСНЕНИЕ:"):
                explanation_parts.append(stripped.split(":", 1)[1].strip())
                capturing = True
            elif capturing and stripped:
                explanation_parts.append(stripped)

        is_correct = "НЕВЕРНО" not in verdict and "ВЕРНО" in verdict
        explanation = " ".join(explanation_parts).strip() or text.strip()
        return is_correct, explanation
    except Exception as e:
        print(f"[Ошибка проверки ответа викторины] {e}")
        return False, "Не удалось проверить ответ, сэр."


def start_quiz(topic=None):
    """Начинает сессию минимум из TARGET_QUESTIONS вопросов подряд: по заданной теме,
    если она указана, иначе по случайному сохранённому конспекту."""
    global current_quiz_question, current_quiz_answer, current_topic
    global questions_asked, correct_count

    source = topic if topic else _load_random_note_content()
    if not source:
        speak(
            "У меня пока нет ни темы, ни сохранённых конспектов для викторины, сэр. "
            "Сначала что-нибудь изучите или назовите тему."
        )
        return

    current_topic = source
    questions_asked = 0
    correct_count = 0

    question, answer = _generate_quiz_question(current_topic)
    if not question:
        speak("Не удалось составить вопрос, сэр.")
        current_quiz_question = None
        current_quiz_answer = None
        return

    current_quiz_question = question
    current_quiz_answer = answer
    speak(f"Начинаем викторину, сэр — будет {TARGET_QUESTIONS} вопросов. Вопрос 1: {question}")


def submit_quiz_answer(user_answer):
    """Проверяет устный ответ, сразу говорит верно/неверно (+ правильный ответ, если
    ошиблись), и автоматически переходит к следующему вопросу — пока не наберётся
    минимум TARGET_QUESTIONS вопросов, либо пока не скажут остановить викторину."""
    global current_quiz_question, current_quiz_answer, current_topic
    global questions_asked, correct_count

    if not current_quiz_question:
        speak("Сначала начните викторину, сэр.")
        return

    if is_quiz_stop_request(user_answer):
        _finish_quiz()
        return

    is_correct, explanation = _evaluate_answer(current_quiz_question, current_quiz_answer, user_answer)
    questions_asked += 1
    stats.increment("quizzes_taken")

    if is_correct:
        correct_count += 1
        speak(f"Верно! {explanation}")
    else:
        speak(f"Неверно. {explanation}")

    if questions_asked >= TARGET_QUESTIONS:
        _finish_quiz()
        return

    next_question, next_answer = _generate_quiz_question(current_topic)
    if not next_question:
        speak("Не удалось составить следующий вопрос, сэр. На этом закончим викторину.")
        _finish_quiz()
        return

    current_quiz_question = next_question
    current_quiz_answer = next_answer
    speak(f"Вопрос {questions_asked + 1}: {next_question}")


def _finish_quiz():
    """Завершает сессию викторины и подводит итог."""
    global current_quiz_question, current_quiz_answer, current_topic
    global questions_asked, correct_count

    speak(f"Викторина завершена, сэр. Правильных ответов: {correct_count} из {questions_asked}.")
    current_quiz_question = None
    current_quiz_answer = None
    current_topic = None