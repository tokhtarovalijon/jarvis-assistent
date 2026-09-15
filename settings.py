"""
Пользовательские настройки: голос озвучки, требуется ли wake word "Джарвис".
Хранятся в JSON-файле, редактируются через окно настроек в интерфейсе.
"""
import os
import json

SETTINGS_FILE = "настройки.json"

DEFAULT_SETTINGS = {
    "tts_voice": "ru-RU-DmitryNeural",
    "require_wake_word": True,
}

# Отображаемое имя -> техническое имя голоса edge-tts
# Первые два — нативные русские голоса, звучат надёжно и правильно.
# Остальные — мультиязычные голоса (не русские по происхождению), для русского текста
# это ЭКСПЕРИМЕНТАЛЬНО: могут звучать с сильным акцентом, необычно, или вообще не
# сработать. Если голос откажет — Джарвис сам переключится на резервный движок.
VOICE_OPTIONS = {
    "Дмитрий (рус., муж.)": "ru-RU-DmitryNeural",
    "Светлана (рус., жен.)": "ru-RU-SvetlanaNeural",
    "Аврора (эксперим., жен.)": "en-US-AvaMultilingualNeural",
    "Орион (эксперим., муж.)": "en-US-AndrewMultilingualNeural",
}

_settings = None


def load_settings():
    global _settings
    if _settings is not None:
        return _settings
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            _settings = {**DEFAULT_SETTINGS, **loaded}
        except Exception as e:
            print(f"[Ошибка загрузки настроек] {e}")
            _settings = dict(DEFAULT_SETTINGS)
    else:
        _settings = dict(DEFAULT_SETTINGS)
    return _settings


def save_settings(new_settings):
    global _settings
    _settings = {**DEFAULT_SETTINGS, **new_settings}
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(_settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Ошибка сохранения настроек] {e}")


def get(key):
    return load_settings().get(key, DEFAULT_SETTINGS.get(key))


def set_value(key, value):
    s = load_settings()
    s[key] = value
    save_settings(s)