"""
"Самообучение": Джарвис постепенно накапливает знания по темам за пределами экономики.

Как это работает на самом деле (важно понимать честно):
- Это НЕ дообучение самой нейросети — переобучать саму модель дорого и сложно, и для
  личного проекта не нужно.
- Вместо этого Джарвис ведёт персональную базу знаний поверх общей модели: каждый раз,
  когда вы спрашиваете что-то по новой теме, он определяет предмет и сохраняет из
  ответа 1-2 ключевых факта. В следующий раз, когда спросите что-то по этой же теме,
  накопленные факты добавляются в контекст запроса — ответы становятся более
  последовательными и информированными с каждым разом.
- Для экономики по-прежнему используется отдельная, более надёжная система (20
  классических трудов, см. ECONOMIC_SOURCES в ai.py) — самообучение подключается
  для ВСЕХ ОСТАЛЬНЫХ тем.
"""
import os
import json

from config import client

KNOWLEDGE_FILE = "база_знаний.json"


def _load_kb():
    if not os.path.exists(KNOWLEDGE_FILE):
        return {}
    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_kb(kb):
    try:
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(kb, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Ошибка сохранения базы знаний] {e}")


def detect_subject(question):
    """Определяет учебный предмет вопроса одним словом (история, право, биология и т.п.)."""
    if not client:
        return "общее"
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Определи учебный предмет вопроса ОДНИМ словом на русском в "
                        "именительном падеже (например: экономика, история, право, "
                        "математика, биология, философия, психология, физика). "
                        "Ответь только этим словом, без пояснений и точки."
                    ),
                },
                {"role": "user", "content": question},
            ],
            temperature=0,
            max_tokens=10,
        )
        subject = response.choices[0].message.content.strip().lower().strip(".")
        return subject or "общее"
    except Exception as e:
        print(f"[Ошибка определения предмета] {e}")
        return "общее"


def get_subject_context(subject, limit=10):
    """Возвращает накопленные факты по предмету в виде текста для контекста ИИ.
    Если по теме ничего ещё не накоплено — вернёт пустую строку."""
    kb = _load_kb()
    facts = kb.get(subject, [])
    if not facts:
        return ""
    recent = facts[-limit:]
    return (
        f"Ранее вы уже обсуждали тему «{subject}». Вот факты из прошлых разговоров "
        "(используй для согласованности с уже сказанным, не повторяй их дословно):\n"
        + "\n".join(f"- {f}" for f in recent)
    )


def learn_from_answer(subject, question, answer):
    """Извлекает 1-2 ключевых факта из ответа и добавляет их в базу знаний по предмету —
    это и есть 'самообучение': база растёт с каждым новым вопросом по теме."""
    if not client:
        return
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Извлеки из ответа 1-2 самых важных и компактных факта (по одному "
                        "предложению каждый) для сохранения в базу знаний на будущее. "
                        "Ответь только фактами, каждый на новой строке, без нумерации "
                        "и пояснений."
                    ),
                },
                {"role": "user", "content": f"Вопрос: {question}\nОтвет: {answer}"},
            ],
            temperature=0.2,
            max_tokens=200,
        )
        raw_facts = response.choices[0].message.content.splitlines()
        new_facts = [line.strip("- ").strip() for line in raw_facts if line.strip()]
        if not new_facts:
            return

        kb = _load_kb()
        kb.setdefault(subject, [])
        for fact in new_facts:
            if fact not in kb[subject]:
                kb[subject].append(fact)
        kb[subject] = kb[subject][-100:]  # не даём файлу расти бесконечно
        _save_kb(kb)
    except Exception as e:
        print(f"[Ошибка самообучения] {e}")


def get_summary():
    """Голосовая сводка того, что Джарвис уже 'выучил' сверх базовых знаний."""
    kb = _load_kb()
    if not kb:
        return "Пока я ничего не выучил сверх базовых знаний, сэр. Задавайте вопросы по разным темам."
    parts = [f"{subject} ({len(facts)} фактов)" for subject, facts in kb.items()]
    return "Я постепенно изучил: " + "; ".join(parts) + "."
