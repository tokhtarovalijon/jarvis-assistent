"""
Расписание и дедлайны: добавление событий голосом (дата/время распознаёт ИИ),
просмотр расписания и фоновые напоминания за 15 минут до события.
"""
import os
import json
import threading
import time
from datetime import datetime, timedelta

from config import client
from tts import speak

SCHEDULE_FILE = "расписание.json"

SCHEDULE_ADD_TRIGGERS = [
    "добавь пару", "добавь дедлайн", "добавь событие", "запомни дедлайн", "добавь занятие",
]
SCHEDULE_SHOW_TODAY_TRIGGERS = ["что у меня сегодня", "мои пары сегодня"]
SCHEDULE_SHOW_TOMORROW_TRIGGERS = ["что у меня завтра", "мои пары завтра"]
SCHEDULE_SHOW_ALL_TRIGGERS = ["мои дедлайны", "моё расписание", "покажи расписание"]


def is_schedule_add_request(text):
    return any(t in text for t in SCHEDULE_ADD_TRIGGERS)


def is_schedule_show_today(text):
    return any(t in text for t in SCHEDULE_SHOW_TODAY_TRIGGERS)


def is_schedule_show_tomorrow(text):
    return any(t in text for t in SCHEDULE_SHOW_TOMORROW_TRIGGERS)


def is_schedule_show_all(text):
    return any(t in text for t in SCHEDULE_SHOW_ALL_TRIGGERS)


def _load_events():
    if not os.path.exists(SCHEDULE_FILE):
        return []
    try:
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_events(events):
    try:
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Ошибка сохранения расписания] {e}")


def _parse_event_with_ai(user_text):
    """Просит ИИ извлечь название события и точные дату/время из фразы пользователя."""
    if not client:
        return None
    now = datetime.now()
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Сегодня {now.strftime('%Y-%m-%d')}, время сейчас {now.strftime('%H:%M')}. "
                        "Извлеки из фразы пользователя название события и точные дату и время. "
                        "Ответь СТРОГО в формате:\n"
                        "НАЗВАНИЕ: <короткое название>\n"
                        "ДАТА: <YYYY-MM-DD>\n"
                        "ВРЕМЯ: <HH:MM>\n"
                        "Если время не указано явно, поставь 09:00. Если дата не указана явно, "
                        "используй завтрашнюю дату."
                    ),
                },
                {"role": "user", "content": user_text},
            ],
            temperature=0.1,
            max_tokens=150,
        )
        text = response.choices[0].message.content
        title, date_str, time_str = None, None, None
        for line in text.splitlines():
            line = line.strip()
            if line.upper().startswith("НАЗВАНИЕ:"):
                title = line.split(":", 1)[1].strip()
            elif line.upper().startswith("ДАТА:"):
                date_str = line.split(":", 1)[1].strip()
            elif line.upper().startswith("ВРЕМЯ:"):
                time_str = line.split(":", 1)[1].strip()
        if not (title and date_str and time_str):
            return None
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        return {"title": title, "datetime": dt.isoformat()}
    except Exception as e:
        print(f"[Ошибка разбора события] {e}")
        return None


def add_event(user_text):
    event = _parse_event_with_ai(user_text)
    if not event:
        speak("Не удалось разобрать дату и время события, сэр. Попробуйте сказать точнее, например: "
              "'добавь пару по экономике завтра в 10 утра'.")
        return
    events = _load_events()
    events.append(event)
    _save_events(events)
    dt = datetime.fromisoformat(event["datetime"])
    speak(f"Записал: {event['title']} — {dt.strftime('%d.%m.%Y в %H:%M')}, сэр.")


def _show_for_date(target_date, label):
    events = _load_events()
    matching = [e for e in events if datetime.fromisoformat(e["datetime"]).date() == target_date]
    if not matching:
        speak(f"На {label} ничего не запланировано, сэр.")
        return
    matching.sort(key=lambda e: e["datetime"])
    parts = [f"{datetime.fromisoformat(e['datetime']).strftime('%H:%M')} — {e['title']}" for e in matching]
    speak(f"На {label}: " + "; ".join(parts))


def show_today():
    _show_for_date(datetime.now().date(), "сегодня")


def show_tomorrow():
    _show_for_date((datetime.now() + timedelta(days=1)).date(), "завтра")


def show_upcoming():
    events = _load_events()
    now = datetime.now()
    upcoming = [e for e in events if datetime.fromisoformat(e["datetime"]) >= now]
    if not upcoming:
        speak("Ближайших дедлайнов нет, сэр.")
        return
    upcoming.sort(key=lambda e: e["datetime"])
    parts = [
        f"{e['title']} — {datetime.fromisoformat(e['datetime']).strftime('%d.%m в %H:%M')}"
        for e in upcoming[:5]
    ]
    speak("Ближайшие события: " + "; ".join(parts))


# --- ФОНОВЫЕ НАПОМИНАНИЯ ---
_notified_events = set()


def _reminder_loop():
    """Проверяет раз в минуту, не пора ли напомнить о событии (за 15 минут до него)."""
    while True:
        try:
            events = _load_events()
            now = datetime.now()
            for e in events:
                event_time = datetime.fromisoformat(e["datetime"])
                minutes_left = (event_time - now).total_seconds() / 60
                event_key = e["title"] + e["datetime"]
                if 0 <= minutes_left <= 15 and event_key not in _notified_events:
                    speak(f"Напоминаю, сэр: через {int(minutes_left)} мин. — {e['title']}.")
                    _notified_events.add(event_key)
        except Exception as ex:
            print(f"[Ошибка проверки напоминаний] {ex}")
        time.sleep(60)


def start_reminder_thread():
    threading.Thread(target=_reminder_loop, daemon=True).start()