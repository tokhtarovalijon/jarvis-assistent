"""
Графический интерфейс J.A.R.V.I.S. — HUD-стиль (тёмно-синий/оранжевый, реактор с анимацией),
журнал общения, поле текстового ввода и кнопки быстрого доступа.
"""
import os
import threading
import math
from datetime import datetime
import customtkinter as ctk

from config import (
    COLOR_BG, COLOR_PANEL, COLOR_PANEL_DARK, COLOR_BORDER,
    COLOR_BLUE, COLOR_CYAN, COLOR_MUTED,
)
from runtime_state import stop_speech_event
from tts import speak
from speech import listen
from commands import process_commands, handle_typed_command
import settings


class JARVISApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("⚡ J.A.R.V.I.S. AI SYSTEM ⚡")
        self.root.geometry("520x830")
        self.root.resizable(True, True)
        self.root.minsize(420, 600)
        self.root.configure(fg_color=COLOR_BG)

        try:
            self.root.iconbitmap("jarvis_icon.ico")
        except Exception as e:
            print(f"[Иконка] Не удалось установить иконку окна: {e}")

        # --- ВЕРХНЯЯ ПОЛОСА-АКЦЕНТ ---
        self.top_strip = ctk.CTkFrame(self.root, fg_color=COLOR_BORDER, height=3)
        self.top_strip.pack(fill="x", padx=0, pady=(0, 0))

        # --- ВЕРХНЯЯ ПАНЕЛЬ ---
        self.header_frame = ctk.CTkFrame(
            self.root, fg_color=COLOR_PANEL, height=90,
            border_width=1, border_color=COLOR_BORDER,
        )
        self.header_frame.pack(fill="x", padx=10, pady=(10, 0))
        self.header_frame.pack_propagate(False)

        self.title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_box.pack(side="left", padx=20, pady=10)

        self.title_label = ctk.CTkLabel(
            self.title_box,
            text="⚡ J.A.R.V.I.S.",
            font=("Consolas", 26, "bold"),
            text_color=COLOR_BORDER,
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            self.title_box,
            text="СИСТЕМА ИСКУССТВЕННОГО ИНТЕЛЛЕКТА",
            font=("Consolas", 10),
            text_color=COLOR_BLUE,
        )
        self.subtitle_label.pack(anchor="w")

        self.clock_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.clock_box.pack(side="right", padx=20, pady=10)

        self.clock_label = ctk.CTkLabel(
            self.clock_box,
            text="00:00:00",
            font=("Consolas", 20, "bold"),
            text_color=COLOR_CYAN,
        )
        self.clock_label.pack(anchor="e")

        self.date_label = ctk.CTkLabel(
            self.clock_box,
            text="",
            font=("Consolas", 10),
            text_color=COLOR_MUTED,
        )
        self.date_label.pack(anchor="e")
        self.update_clock()

        # --- РЕАКТОР (Анимированное ядро, адаптивный размер) ---
        self.canvas = ctk.CTkCanvas(
            self.root, width=260, height=260, bg=COLOR_BG, highlightthickness=0
        )
        self.canvas.pack(pady=(20, 5), fill="both", expand=True)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        self.current_color = COLOR_BLUE
        self.angle = 0
        self.pulse = 0
        self.draw_reactor()
        self.animate_reactor()

        # --- СТАТУС ---
        self.status_frame = ctk.CTkFrame(
            self.root, fg_color=COLOR_PANEL, height=58,
            border_width=1, border_color=COLOR_BORDER,
        )
        self.status_frame.pack(fill="x", padx=10, pady=8)
        self.status_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="🔵 РЕЖИМ ОЖИДАНИЯ",
            font=("Consolas", 13, "bold"),
            text_color=COLOR_BLUE,
        )
        self.status_label.pack(pady=(6, 0))

        self.hint_label = ctk.CTkLabel(
            self.status_frame,
            text='Скажите "Джарвис" перед командой  •  Esc — прервать речь',
            font=("Consolas", 9),
            text_color=COLOR_MUTED,
        )
        self.hint_label.pack(pady=(0, 4))

        # --- ЧАТ ЛОГ ---
        self.chat_frame = ctk.CTkFrame(
            self.root, fg_color=COLOR_PANEL,
            border_width=1, border_color=COLOR_BORDER,
        )
        self.chat_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.log_label = ctk.CTkLabel(
            self.chat_frame,
            text="📡 ЖУРНАЛ СВЯЗИ",
            font=("Consolas", 11, "bold"),
            text_color=COLOR_BORDER,
        )
        self.log_label.pack(anchor="w", padx=12, pady=(8, 0))

        self.chat_box = ctk.CTkTextbox(
            self.chat_frame,
            width=480,
            height=340,
            font=("Consolas", 13),
            text_color=COLOR_CYAN,
            fg_color=COLOR_PANEL_DARK,
            border_width=1,
            border_color="#1A2A4A",
        )
        self.chat_box.pack(fill="both", expand=True, padx=8, pady=8)
        self.chat_box.configure(state="disabled")

        # --- ПОЛЕ ВВОДА ТЕКСТА (альтернатива голосу) ---
        self.input_frame = ctk.CTkFrame(self.root, fg_color=COLOR_PANEL, height=50)
        self.input_frame.pack(fill="x", padx=10, pady=(0, 8))
        self.input_frame.pack_propagate(False)

        self.text_input = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Напишите команду и нажмите Enter...",
            font=("Consolas", 13),
            fg_color=COLOR_PANEL_DARK,
            text_color=COLOR_CYAN,
            border_color=COLOR_BORDER,
            border_width=1,
        )
        self.text_input.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        self.text_input.bind("<Return>", self.send_typed_command)

        self.btn_send = ctk.CTkButton(
            self.input_frame,
            text="➤",
            width=40,
            command=self.send_typed_command,
            fg_color=COLOR_PANEL_DARK,
            hover_color="#1E3550",
            text_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            font=("Consolas", 14, "bold"),
        )
        self.btn_send.pack(side="right", padx=(0, 10), pady=10)

        # --- НИЖНЯЯ ПАНЕЛЬ С КНОПКАМИ (2 ряда по 2, чтобы все помещались) ---
        self.bottom_frame = ctk.CTkFrame(self.root, fg_color=COLOR_PANEL, height=104)
        self.bottom_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.bottom_frame.pack_propagate(False)

        btn_style = {
            "fg_color": COLOR_PANEL_DARK,
            "hover_color": "#1E3550",
            "text_color": COLOR_BORDER,
            "border_width": 1,
            "border_color": COLOR_BORDER,
            "font": ("Consolas", 12, "bold"),
        }

        self.btn_row1 = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.btn_row1.pack(fill="x")

        self.btn_row2 = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.btn_row2.pack(fill="x")

        self.btn_status = ctk.CTkButton(
            self.btn_row1, text="⟳ СТАТУС", command=self.show_status, **btn_style
        )
        self.btn_status.pack(side="left", padx=10, pady=(10, 5), expand=True, fill="x")

        self.btn_clear = ctk.CTkButton(
            self.btn_row1, text="⌫ ОЧИСТИТЬ", command=self.clear_chat, **btn_style
        )
        self.btn_clear.pack(side="left", padx=10, pady=(10, 5), expand=True, fill="x")

        self.btn_voice = ctk.CTkButton(
            self.btn_row2, text="🎤 МИКРОФОН", command=self.test_mic, **btn_style
        )
        self.btn_voice.pack(side="left", padx=10, pady=(5, 10), expand=True, fill="x")

        self.btn_settings = ctk.CTkButton(
            self.btn_row2, text="⚙ НАСТРОЙКИ", command=self.open_settings, **btn_style
        )
        self.btn_settings.pack(side="left", padx=10, pady=(5, 10), expand=True, fill="x")

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind("<Escape>", self.interrupt_speech)
        self.root.focus_set()

        # Запуск потока голосового управления
        self.thread = threading.Thread(target=process_commands, daemon=True)
        self.thread.start()

    def update_clock(self):
        now = datetime.now()
        self.clock_label.configure(text=now.strftime("%H:%M:%S"))
        self.date_label.configure(text=now.strftime("%d.%m.%Y"))
        self.root.after(1000, self.update_clock)

    def draw_reactor(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 20 or h < 20:
            # Окно ещё не отрисовано (например, при самом первом запуске) — пропускаем кадр
            return
        cx, cy = w // 2, h // 2
        # Радиус — доля от меньшей стороны, но не больше 140px, чтобы на весь экран
        # реактор не раздувался до нелепых размеров — лишнее место возьмёт чат.
        radius = max(40, min(140, int(min(w, h) * 0.32)))

        # --- Мягкое внешнее свечение ---
        r, g, b = self.hex_to_rgb(self.current_color)
        glow_color = f"#{r:02x}{g:02x}{b:02x}"
        for i in range(14, 0, -1):
            self.canvas.create_oval(
                cx - radius - i * 2, cy - radius - i * 2,
                cx + radius + i * 2, cy + radius + i * 2,
                outline=glow_color, width=1, stipple="gray25",
            )

        # --- Внешнее тонкое кольцо (статичное, приглушённого цвета) ---
        self.canvas.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius,
            outline=COLOR_MUTED, width=1,
        )

        # --- Пульсирующее основное кольцо ---
        pulse_offset = int(4 * math.sin(self.pulse))
        ring_radius = radius - 12 + pulse_offset
        self.canvas.create_oval(
            cx - ring_radius, cy - ring_radius,
            cx + ring_radius, cy + ring_radius,
            outline=self.current_color, width=3,
        )

        # --- Внутренний тёмный круг-подложка под букву ---
        core_radius = max(15, radius - 28)
        self.canvas.create_oval(
            cx - core_radius, cy - core_radius,
            cx + core_radius, cy + core_radius,
            fill=COLOR_PANEL_DARK, outline=self.current_color, width=2,
        )

        # --- Буква "J" по центру (размер шрифта тоже масштабируется) ---
        letter_size = max(20, int(radius * 0.55))
        self.canvas.create_text(
            cx, cy, text="J", fill=self.current_color, font=("Segoe UI", letter_size, "bold")
        )

        # --- Название под значком ---
        self.canvas.create_text(
            cx, cy + radius + 22, text="JARVIS",
            fill=COLOR_MUTED, font=("Consolas", 12, "bold"),
        )

    def on_canvas_resize(self, event=None):
        self.draw_reactor()

    def animate_reactor(self):
        self.pulse += 0.05
        self.draw_reactor()
        self.root.after(80, self.animate_reactor)

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def update_reactor_color(self, color):
        self.current_color = color

    def update_gui_status(self, text, color="#FFFFFF"):
        self.status_label.configure(text=text, text_color=color)

    def append_chat_log(self, text):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", text)
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def show_status(self):
        self.append_chat_log(f"🛰️ Система активна — {datetime.now().strftime('%H:%M:%S')}\n")
        speak("Все системы работают штатно, сэр.")

    def clear_chat(self):
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")
        self.append_chat_log("🧹 Чат очищен\n")

    def test_mic(self):
        self.append_chat_log("🎤 Тестирование микрофона...\n")
        speak("Проверка микрофона. Скажите что-нибудь, сэр.")
        query = listen()
        if query:
            self.append_chat_log(f"✅ Микрофон работает: {query}\n")
            speak(f"Услышал: {query}")
        else:
            self.append_chat_log("❌ Микрофон не отвечает\n")
            speak("Микрофон не отвечает, проверьте подключение.")

    def interrupt_speech(self, event=None):
        stop_speech_event.set()
        self.append_chat_log("⏹ Джарвис прерван (Esc), сэр.\n")

    def open_settings(self):
        window = ctk.CTkToplevel(self.root)
        window.title("⚙ Настройки")
        window.geometry("380x260")
        window.configure(fg_color=COLOR_BG)
        window.attributes("-topmost", True)

        ctk.CTkLabel(
            window, text="Голос озвучки", font=("Consolas", 13, "bold"), text_color=COLOR_BORDER
        ).pack(pady=(20, 5))

        current_voice_id = settings.get("tts_voice")
        current_voice_name = next(
            (name for name, vid in settings.VOICE_OPTIONS.items() if vid == current_voice_id),
            list(settings.VOICE_OPTIONS.keys())[0],
        )
        voice_var = ctk.StringVar(value=current_voice_name)
        voice_menu = ctk.CTkOptionMenu(
            window, values=list(settings.VOICE_OPTIONS.keys()), variable=voice_var,
            fg_color=COLOR_PANEL_DARK, button_color=COLOR_BORDER, button_hover_color="#1E3550",
        )
        voice_menu.pack(pady=(0, 20))

        wake_word_var = ctk.BooleanVar(value=settings.get("require_wake_word"))
        wake_word_check = ctk.CTkCheckBox(
            window, text='Требовать "Джарвис" перед командой', variable=wake_word_var,
            font=("Consolas", 12), text_color=COLOR_CYAN,
            fg_color=COLOR_BORDER, hover_color="#1E3550",
        )
        wake_word_check.pack(pady=(0, 25))

        def save_and_close():
            settings.set_value("tts_voice", settings.VOICE_OPTIONS[voice_var.get()])
            settings.set_value("require_wake_word", bool(wake_word_var.get()))
            self.append_chat_log("⚙ Настройки сохранены, сэр.\n")
            window.destroy()

        ctk.CTkButton(
            window, text="Сохранить", command=save_and_close,
            fg_color=COLOR_PANEL_DARK, hover_color="#1E3550",
            text_color=COLOR_BORDER, border_width=1, border_color=COLOR_BORDER,
            font=("Consolas", 12, "bold"),
        ).pack()

    def send_typed_command(self, event=None):
        text = self.text_input.get()
        if not text.strip():
            return
        self.text_input.delete(0, "end")
        handle_typed_command(text)

    def on_closing(self):
        os._exit(0)