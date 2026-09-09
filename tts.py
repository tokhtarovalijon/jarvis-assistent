"""
Озвучка ответов Джарвиса: облачный голос (edge_tts) с резервным локальным движком (pyttsx3),
потоковое воспроизведение по предложениям для длинных ответов, прерывание клавишей Esc.
"""
import os
import asyncio
import re
import threading
import queue
import edge_tts
import pygame
import pyttsx3

from config import BOT_NAME, COLOR_SPEAK, COLOR_BLUE
from runtime_state import stop_speech_event, is_voice_output_enabled, append_chat_log, update_reactor_color

pygame.mixer.init()

# pyttsx3 инициализируется лениво (только если реально понадобится резервная озвучка) —
# его запуск на Windows (через SAPI5/COM) может занимать заметное время при старте программы.
_offline_engine = None


def get_offline_engine():
    global _offline_engine
    if _offline_engine is None:
        _offline_engine = pyttsx3.init()
    return _offline_engine


# --- ОЗВУЧКА ---
async def generate_audio(text, output_file="voice.mp3"):
    communicate = edge_tts.Communicate(text, voice="ru-RU-DmitryNeural")
    await communicate.save(output_file)


def split_sentences(text):
    """Разбивает текст на предложения для потоковой озвучки длинных ответов."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s]


def _play_single_file(path):
    """Проигрывает один mp3-файл, реагируя на прерывание (Esc)."""
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        if stop_speech_event.is_set():
            pygame.mixer.music.stop()
            break
        pygame.time.Clock().tick(10)
    pygame.mixer.music.unload()


def _speak_fallback_offline(text):
    """Резервная озвучка через локальный движок, если облачный TTS недоступен."""
    try:
        offline_engine = get_offline_engine()
        offline_engine.say(text)
        offline_engine.runAndWait()
    except Exception as e2:
        print(f"[Резервный TTS тоже не сработал] {e2}")


def speak(text):
    print(f"\n{BOT_NAME}: {text}")
    append_chat_log(f"Джарвис: {text}\n")

    if not is_voice_output_enabled():
        return

    update_reactor_color(COLOR_SPEAK)
    stop_speech_event.clear()

    chunks = split_sentences(text) if len(text) > 150 else [text]

    if len(chunks) <= 1:
        # Короткая фраза — озвучиваем как есть, без усложнений
        try:
            asyncio.run(generate_audio(text, "voice.mp3"))
            _play_single_file("voice.mp3")
            if os.path.exists("voice.mp3"):
                os.remove("voice.mp3")
        except Exception as e:
            print(f"[TTS ошибка, использую резервный движок] {e}")
            _speak_fallback_offline(text)
        update_reactor_color(COLOR_BLUE)
        return

    # Длинный ответ: генерируем аудио следующего предложения ПОКА играет текущее.
    audio_queue = queue.Queue(maxsize=2)
    generation_done = threading.Event()
    generation_failed = threading.Event()

    def producer():
        for i, chunk in enumerate(chunks):
            if stop_speech_event.is_set():
                break
            audio_file = os.path.join(os.getcwd(), f"voice_{i}.mp3")
            try:
                asyncio.run(generate_audio(chunk, audio_file))
                audio_queue.put(audio_file)
            except Exception as e:
                print(f"[Ошибка генерации аудио для фрагмента {i}] {e}")
                generation_failed.set()
        generation_done.set()

    producer_thread = threading.Thread(target=producer, daemon=True)
    producer_thread.start()

    played_anything = False
    while True:
        if stop_speech_event.is_set():
            break
        try:
            audio_file = audio_queue.get(timeout=0.2)
        except queue.Empty:
            if generation_done.is_set() and audio_queue.empty():
                break
            continue

        played_anything = True
        try:
            _play_single_file(audio_file)
        except Exception as e:
            print(f"[Ошибка воспроизведения фрагмента] {e}")
        finally:
            if os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                except Exception:
                    pass

    if not played_anything and generation_failed.is_set() and not stop_speech_event.is_set():
        # Облачная озвучка совсем не сработала — читаем весь текст локальным движком
        _speak_fallback_offline(text)

    update_reactor_color(COLOR_BLUE)
