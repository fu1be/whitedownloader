import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import threading
import os
import sys
import re
import pyglet

# ================== НАСТРОЙКИ ПУТЕЙ ==================
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

YTDLP_PATH = os.path.join(BASE_DIR, "yt-dlp.exe")

# ================== ЗАГРУЗКА ШРИФТОВ ==================
# Имена, которые мы будем использовать в коде
FONT_NAME_HEADER = "resotyg"
FONT_NAME_TEXT = "threat"
FALLBACK_FONT = "Segoe UI"

def load_custom_fonts():
    """Загружает шрифты из папки с программой. Возвращает имена для использования."""
    fonts_to_load = {
        "resotyg": ["resotyg.ttf", "resotyg.otf", "Resotyg.ttf", "Resotyg.otf"],
        "threat": ["threat.ttf", "threat.otf", "Threat.ttf", "Threat.otf"]
    }
    
    loaded_names = {}
    
    for name, files in fonts_to_load.items():
        font_loaded = False
        for f in files:
            path = os.path.join(BASE_DIR, f)
            if os.path.exists(path):
                try:
                    pyglet.font.add_file(path)
                    # В pyglet имя шрифта берется из самого файла.
                    # Но мы попробуем использовать имя файла без расширения как запасной вариант.
                    loaded_names[name] = name 
                    font_loaded = True
                    break
                except Exception as e:
                    print(f"Ошибка загрузки шрифта {f}: {e}")
        
        if not font_loaded:
            loaded_names[name] = FALLBACK_FONT
            
    return loaded_names

# Загружаем шрифты и получаем их имена
FONTS = load_custom_fonts()
FONT_HEADER = FONTS.get("resotyg", FALLBACK_FONT)
FONT_TEXT = FONTS.get("threat", FALLBACK_FONT)

# ================== СТИЛИ ==================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Цветовая палитра (ЧБ + красный акцент)
BG_COLOR = "#121212"          
CARD_COLOR = "#1E1E1E"        
TEXT_COLOR = "#FFFFFF"        
SUBTEXT_COLOR = "#A0A0A0"     
ACCENT_COLOR = "#E53935"      
ACCENT_HOVER = "#C62828"      
ENTRY_BG = "#2A2A2A"          

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("whitedownloader")
        self.geometry("850x700")
        self.minsize(750, 650)
        self.configure(fg_color=BG_COLOR)

        self.save_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads", "whitedownloader"))
        self.is_downloading = False

        # --- Заголовок ---
        self.header = ctk.CTkLabel(
            self, text="whitedownloader", 
            font=ctk.CTkFont(family=FONT_HEADER, size=32, weight="bold"),
            text_color=TEXT_COLOR
        )
        self.header.pack(pady=(25, 5))

        self.subtitle = ctk.CTkLabel(
            self, text="Скачивайте видео с YouTube, Twitch и TikTok",
            font=ctk.CTkFont(family=FONT_TEXT, size=14),
            text_color=SUBTEXT_COLOR
        )
        self.subtitle.pack(pady=(0, 25))

        # --- Карточка 1: Ссылка ---
        self.card_url = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=15)
        self.card_url.pack(fill="x", padx=40, pady=10)

        self.label_url = ctk.CTkLabel(self.card_url, text="Ссылка на видео", font=ctk.CTkFont(family=FONT_TEXT, size=14, weight="bold"), text_color=TEXT_COLOR)
        self.label_url.pack(anchor="w", padx=20, pady=(15, 5))

        self.entry_url = ctk.CTkEntry(
            self.card_url, placeholder_text="https://www.youtube.com/watch?v=...",
            height=45, font=ctk.CTkFont(size=14),
            fg_color=ENTRY_BG, border_color="#333333", text_color=TEXT_COLOR
        )
        self.entry_url.pack(fill="x", padx=20, pady=(0, 20))

        # --- Карточка 2: Путь сохранения ---
        self.card_path = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=15)
        self.card_path.pack(fill="x", padx=40, pady=10)

        self.label_path = ctk.CTkLabel(self.card_path, text="Папка для сохранения", font=ctk.CTkFont(family=FONT_TEXT, size=14, weight="bold"), text_color=TEXT_COLOR)
        self.label_path.pack(anchor="w", padx=20, pady=(15, 5))

        self.path_frame = ctk.CTkFrame(self.card_path, fg_color="transparent")
        self.path_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.entry_path = ctk.CTkEntry(
            self.path_frame, textvariable=self.save_path, height=45,
            font=ctk.CTkFont(size=13), state="readonly",
            fg_color=ENTRY_BG, border_color="#333333", text_color=SUBTEXT_COLOR
        )
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_browse = ctk.CTkButton(
            self.path_frame, text="Обзор", width=90, height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#333333", hover_color="#444444", text_color=TEXT_COLOR,
            command=self.browse_folder
        )
        self.btn_browse.pack(side="right")

        # --- Карточка 3: Время ---
        self.card_time = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=15)
        self.card_time.pack(fill="x", padx=40, pady=10)

        self.label_time = ctk.CTkLabel(self.card_time, text="Отрезок (необязательно)", font=ctk.CTkFont(family=FONT_TEXT, size=14, weight="bold"), text_color=TEXT_COLOR)
        self.label_time.pack(anchor="w", padx=20, pady=(15, 5))

        self.time_inner = ctk.CTkFrame(self.card_time, fg_color="transparent")
        self.time_inner.pack(fill="x", padx=20, pady=(0, 20))

        self.entry_start = ctk.CTkEntry(self.time_inner, width=120, height=40, placeholder_text="С: 00:00:00", fg_color=ENTRY_BG, border_color="#333333")
        self.entry_start.pack(side="left", padx=(0, 15))

        self.entry_end = ctk.CTkEntry(self.time_inner, width=120, height=40, placeholder_text="По: 00:00:00", fg_color=ENTRY_BG, border_color="#333333")
        self.entry_end.pack(side="left")

        # --- Кнопка Скачать ---
        self.btn_download = ctk.CTkButton(
            self, text="Скачать", height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, text_color=TEXT_COLOR,
            command=self.start_download
        )
        self.btn_download.pack(fill="x", padx=40, pady=25)

        # --- Прогресс-бар ---
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=40, pady=(0, 25))

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, height=12, corner_radius=6,
            fg_color="#2A2A2A", progress_color=ACCENT_COLOR
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x")

        self.progress_label = ctk.CTkLabel(
            self.progress_frame, text="Готов к скачиванию", 
            font=ctk.CTkFont(family=FONT_TEXT, size=12), text_color=SUBTEXT_COLOR
        )
        self.progress_label.pack(pady=(5, 0))

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
        start_time = self.entry_start.get().strip()
        end_time = self.entry_end.get().strip()

        if not url:
            messagebox.showwarning("Внимание", "Вставьте ссылку на видео!")
            return
        if (start_time and not end_time) or (not start_time and end_time):
            messagebox.showwarning("Внимание", "Для отрезка укажите и начало, и конец.")
            return

        self.is_downloading = True
        self.btn_download.configure(state="disabled", text="Скачиваю...", fg_color="#555555")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Подключение к серверу...", text_color=SUBTEXT_COLOR)

        thread = threading.Thread(target=self.download_thread, args=(url, start_time, end_time))
        thread.daemon = True
        thread.start()

    def download_thread(self, url, start_time, end_time):
        service_name, extra_args = self.get_service_folder(url)
        target_folder = os.path.join(self.save_path.get(), service_name)
        
        os.makedirs(target_folder, exist_ok=True)

        args = ["-S", "vcodec:h264,res,acodec:m4a", "--merge-output-format", "mp4", "-N", "16"]
        args.extend(extra_args)

        if start_time and end_time:
            args.extend(["--download-sections", f"*{start_time}-{end_time}"])
            filename = f"%(title)s [{start_time.replace(':','_')}-{end_time.replace(':','_')}].%(ext)s"
        else:
            filename = "%(title)s.%(ext)s"

        output_template = os.path.join(target_folder, filename)
        args.extend(["-o", output_template, url])

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
