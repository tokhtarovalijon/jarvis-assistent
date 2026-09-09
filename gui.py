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


class JARVISApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("⚡ J.A.R.V.I.S. AI SYSTEM ⚡")
        self.root.geometry("520x780")
        self.root.resizable(False, False)
        self.root.configure(fg_color=COLOR_BG)

        # --- ВЕРХНЯЯ ОРАНЖЕВАЯ HUD-ПОЛОСА ---
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

        # --- РЕАКТОР (Анимированное ядро с HUD-уголками) ---
        self.canvas = ctk.CTkCanvas(
            self.root, width=260, height=260, bg=COLOR_BG, highlightthickness=0
        )
        self.canvas.pack(pady=(20, 5))

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

        # --- НИЖНЯЯ ПАНЕЛЬ С КНОПКАМИ ---
        self.bottom_frame = ctk.CTkFrame(self.root, fg_color=COLOR_PANEL, height=54)
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

        self.btn_status = ctk.CTkButton(
            self.bottom_frame, text="⟳ СТАТУС", command=self.show_status, **btn_style
        )
        self.btn_status.pack(side="left", padx=10, pady=10)

        self.btn_clear = ctk.CTkButton(
            self.bottom_frame, text="⌫ ОЧИСТИТЬ", command=self.clear_chat, **btn_style
        )
        self.btn_clear.pack(side="left", padx=10, pady=10)

        self.btn_voice = ctk.CTkButton(
            self.bottom_frame, text="🎤 МИКРОФОН", command=self.test_mic, **btn_style
        )
        self.btn_voice.pack(side="right", padx=10, pady=10)

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
        w, h = 260, 260
        cx, cy = w // 2, h // 2
        radius = 80

        # --- Статичные оранжевые HUD-уголки по краям (targeting HUD) ---
        bracket = 18
        margin = 6
        pts = [
            (margin, margin, 1, 1),               # верх-лево
            (w - margin, margin, -1, 1),           # верх-право
            (margin, h - margin, 1, -1),           # низ-лево
            (w - margin, h - margin, -1, -1),      # низ-право
        ]
        for x, y, dx, dy in pts:
            self.canvas.create_line(x, y, x + bracket * dx, y, fill=COLOR_BORDER, width=3)
            self.canvas.create_line(x, y, x, y + bracket * dy, fill=COLOR_BORDER, width=3)

        # --- Внешнее свечение ---
        for i in range(10, 0, -1):
            r, g, b = self.hex_to_rgb(self.current_color)
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.canvas.create_oval(
                cx - radius - i * 3, cy - radius - i * 3,
                cx + radius + i * 3, cy + radius + i * 3,
                outline=color, width=1, stipple="gray50",
            )

        # --- Вращающееся внешнее оранжевое кольцо с делениями (HUD dial) ---
        outer_radius = radius + 25
        for i in range(0, 360, 15):
            rad = math.radians(i - self.angle * 0.6)
            x1 = cx + (outer_radius - 6) * math.cos(rad)
            y1 = cy + (outer_radius - 6) * math.sin(rad)
            x2 = cx + outer_radius * math.cos(rad)
            y2 = cy + outer_radius * math.sin(rad)
            self.canvas.create_line(x1, y1, x2, y2, fill=COLOR_BORDER, width=2)

        # --- Основное кольцо ---
        self.canvas.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius,
            outline=self.current_color, width=3,
        )

        # --- Внутреннее пульсирующее кольцо ---
        pulse_offset = int(5 * math.sin(self.pulse))
        inner_radius = radius - 20 + pulse_offset
        self.canvas.create_oval(
            cx - inner_radius, cy - inner_radius,
            cx + inner_radius, cy + inner_radius,
            outline=self.current_color, width=2, dash=(5, 3),
        )

        # --- Ядро ---
        core_radius = 25 + int(3 * math.sin(self.pulse))
        r, g, b = self.hex_to_rgb(self.current_color)
        core_color = f"#{r:02x}{g:02x}{b:02x}"
        self.canvas.create_oval(
            cx - core_radius, cy - core_radius,
            cx + core_radius, cy + core_radius,
            fill=core_color, outline="#FFFFFF", width=2,
        )

        # --- Энергетические лучи (внутреннее кольцо, основной цвет) ---
        for i in range(0, 360, 30):
            rad = math.radians(i + self.angle)
            x1 = cx + (radius - 10) * math.cos(rad)
            y1 = cy + (radius - 10) * math.sin(rad)
            x2 = cx + (radius + 15) * math.cos(rad)
            y2 = cy + (radius + 15) * math.sin(rad)
            self.canvas.create_line(x1, y1, x2, y2, fill=self.current_color, width=2, capstyle="round")

        self.canvas.create_text(
            cx, cy + 45, text="JARVIS", fill=self.current_color, font=("Consolas", 13, "bold")
        )

    def animate_reactor(self):
        self.angle = (self.angle + 2) % 360
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

    def send_typed_command(self, event=None):
        text = self.text_input.get()
        if not text.strip():
            return
        self.text_input.delete(0, "end")
        handle_typed_command(text)

    def on_closing(self):
        os._exit(0)
