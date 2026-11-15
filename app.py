import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image
import subprocess
import threading
import os
import sys
import re

# ================== НАСТРОЙКИ ПУТЕЙ ==================
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

YTDLP_PATH = os.path.join(BASE_DIR, "yt-dlp.exe")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png") # Имя файла логотипа

# ================== СТИЛИ ==================
ctk.set_appearance_mode("dark")

# Цветовая палитра (Глубокий черный + Яркий красный)
BG_COLOR = "#0F0F0F"          # Основной фон (почти черный)
CARD_COLOR = "#1A1A1A"        # Фон карточек
TEXT_COLOR = "#FFFFFF"        # Белый текст
SUBTEXT_COLOR = "#888888"     # Серый текст
ACCENT_COLOR = "#FF3B30"      # Яркий красный
ACCENT_HOVER = "#D32F2F"      # Темно-красный при наведении
ENTRY_BG = "#262626"          # Фон полей ввода
BORDER_COLOR = "#333333"      # Цвет рамок

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("whitedownloader")
        self.geometry("750x600")
        self.minsize(650, 550)
        self.configure(fg_color=BG_COLOR)

        # Убираем стандартную рамку Windows для современного вида
        self.overrideredirect(True) 

        self.save_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads", "whitedownloader"))
        self.is_downloading = False

        # --- Кастомный заголовок окна (для перетаскивания) ---
        self.title_bar = ctk.CTkFrame(self, fg_color=BG_COLOR, height=30, corner_radius=0)
        self.title_bar.pack(fill="x", side="top")
        self.title_bar.bind("<Button-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)

        # Кнопки управления окном
        self.btn_close = ctk.CTkButton(self.title_bar, text="✕", width=30, height=30, fg_color="transparent", hover_color="#FF3B30", text_color=SUBTEXT_COLOR, command=self.destroy)
        self.btn_close.pack(side="right", padx=5)
        
        self.btn_min = ctk.CTkButton(self.title_bar, text="—", width=30, height=30, fg_color="transparent", hover_color="#333333", text_color=SUBTEXT_COLOR, command=self.minimize)
        self.btn_min.pack(side="right")

        # --- Логотип ---
        try:
            # Загружаем и масштабируем логотип
            logo_image = Image.open(LOGO_PATH)
            # Масштабируем до нужного размера (ширина 250)
            width_percent = (250 / float(logo_image.size[0]))
            height_size = int((float(logo_image.size[1]) * float(width_percent)))
            logo_image = logo_image.resize((250, height_size), Image.Resampling.LANCZOS)
            
            self.logo_ctk = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(250, height_size))
            self.logo_label = ctk.CTkLabel(self, image=self.logo_ctk, text="")
            self.logo_label.pack(pady=(10, 20))
        except Exception as e:
            # Если логотип не найден, показываем текст
            self.logo_label = ctk.CTkLabel(self, text="whitedownloader", font=ctk.CTkFont(size=32, weight="bold"), text_color=TEXT_COLOR)
            self.logo_label.pack(pady=(20, 20))

        # --- Карточка 1: Ссылка ---
        self.card_url = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
        self.card_url.pack(fill="x", padx=30, pady=8)

        self.label_url = ctk.CTkLabel(self.card_url, text="Ссылка на видео", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_COLOR)
        self.label_url.pack(anchor="w", padx=15, pady=(12, 4))

        self.entry_url = ctk.CTkEntry(
            self.card_url, placeholder_text="https://www.youtube.com/watch?v=...",
            height=40, font=ctk.CTkFont(size=13),
            fg_color=ENTRY_BG, border_width=1, border_color=BORDER_COLOR, text_color=TEXT_COLOR
        )
        self.entry_url.pack(fill="x", padx=15, pady=(0, 15))

        # --- Карточка 2: Путь ---
        self.card_path = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
        self.card_path.pack(fill="x", padx=30, pady=8)

        self.label_path = ctk.CTkLabel(self.card_path, text="Папка для сохранения", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_COLOR)
        self.label_path.pack(anchor="w", padx=15, pady=(12, 4))

        self.path_frame = ctk.CTkFrame(self.card_path, fg_color="transparent")
        self.path_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.entry_path = ctk.CTkEntry(
            self.path_frame, textvariable=self.save_path, height=40,
            font=ctk.CTkFont(size=12), state="readonly",
            fg_color=ENTRY_BG, border_width=1, border_color=BORDER_COLOR, text_color=SUBTEXT_COLOR
        )
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_browse = ctk.CTkButton(
            self.path_frame, text="Обзор", width=80, height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2A2A2A", hover_color="#3A3A3A", text_color=TEXT_COLOR,
            command=self.browse_folder
        )
        self.btn_browse.pack(side="right")

        # --- Кнопка Скачать ---
        self.btn_download = ctk.CTkButton(
            self, text="Скачать", height=50,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, text_color=TEXT_COLOR,
            corner_radius=10,
            command=self.start_download
        )
        self.btn_download.pack(fill="x", padx=30, pady=20)

        # --- Прогресс-бар ---
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=30, pady=(0, 20))

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, height=10, corner_radius=5,
            fg_color="#262626", progress_color=ACCENT_COLOR
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x")

        self.progress_label = ctk.CTkLabel(
            self.progress_frame, text="Готов к скачиванию", 
            font=ctk.CTkFont(size=12), text_color=SUBTEXT_COLOR
        )
        self.progress_label.pack(pady=(6, 0))

    # --- Функции перетаскивания окна ---
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def minimize(self):
        # Чтобы свернуть безрамочное окно, нужно временно вернуть рамку
        self.overrideredirect(False)
        self.iconify()

    # При восстановлении окна снова убираем рамку
    def <Map>(self, event):
        if str(event.widget) == str(self):
            self.overrideredirect(True)

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.save_path.get())
        if folder:
            self.save_path.set(folder)

    def get_service_folder(self, url):
        url_lower = url.lower()
        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "YouTube", ["--extractor-args", "youtube:player-client=default,-tv_simply"]
        elif "twitch.tv" in url_lower:
            return "Twitch", []
        elif "tiktok.com" in url_lower:
            return "TikTok", []
        else:
            return "Other", []

    def start_download(self):
        if self.is_downloading:
            return

        url = self.entry_url.get().strip()

        if not url:
            messagebox.showwarning("Внимание", "Вставьте ссылку на видео!")
            return

        self.is_downloading = True
        self.btn_download.configure(state="disabled", text="Скачиваю...", fg_color="#555555")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Подключение к серверу...", text_color=SUBTEXT_COLOR)

        thread = threading.Thread(target=self.download_thread, args=(url,))
        thread.daemon = True
        thread.start()

    def download_thread(self, url):
        service_name, extra_args = self.get_service_folder(url)
        target_folder = os.path.join(self.save_path.get(), service_name)
        
        os.makedirs(target_folder, exist_ok=True)

        args = ["-S", "vcodec:h264,res,acodec:m4a", "--merge-output-format", "mp4", "-N", "16"]
        args.extend(extra_args)
        args.extend(["-o", os.path.join(target_folder, "%(title)s.%(ext)s"), url])

        cmd = [YTDLP_PATH] + args

        try:
            cmd.insert(1, "--newline") 
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            pattern = re.compile(r"\[download\]\s+([\d\.]+)%\s+of\s+([\d\.]+\w+)\s+at\s+([\d\.]+\w+/s)\s+ETA\s+([\d:]+)")

            for line in process.stdout:
                match = pattern.search(line)
                if match:
                    percent = float(match.group(1)) / 100.0
                    speed = match.group(3)
                    eta = match.group(4)
                    
                    self.progress_bar.set(percent)
                    self.progress_label.configure(
                        text=f"{match.group(1)}% • Скорость: {speed} • Осталось: {eta}",
                        text_color=TEXT_COLOR
                    )
                elif "[ExtractAudio]" in line or "[Merger]" in line:
                    self.progress_label.configure(text="Обработка (склейка/конвертация)...", text_color=SUBTEXT_COLOR)
                    self.progress_bar.set(0.99)

            process.wait()

            if process.returncode == 0:
                self.progress_bar.set(1.0)
                self.progress_label.configure(text="✅ Успешно скачано!", text_color="#4CAF50")
            else:
                self.progress_label.configure(text="❌ Ошибка при скачивании", text_color=ACCENT_COLOR)

        except Exception as e:
            self.progress_label.configure(text=f"❌ Ошибка: {e}", text_color=ACCENT_COLOR)
        finally:
            self.is_downloading = False
            self.btn_download.configure(state="normal", text="Скачать", fg_color=ACCENT_COLOR)

if __name__ == "__main__":
    app = App()
    app.mainloop()
