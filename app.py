import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
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

# ================== СТИЛИ ==================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

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
        self.geometry("850x650")
        self.minsize(750, 600)
        self.configure(fg_color=BG_COLOR)

        self.save_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads", "whitedownloader"))
        self.is_downloading = False

        # --- Заголовок (Стандартный шрифт Segoe UI) ---
        self.header = ctk.CTkLabel(
            self, text="whitedownloader", 
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=TEXT_COLOR
        )
        self.header.pack(pady=(25, 5))

        self.subtitle = ctk.CTkLabel(
            self, text="Скачивайте видео с YouTube, Twitch и TikTok",
            font=ctk.CTkFont(size=14),
            text_color=SUBTEXT_COLOR
        )
        self.subtitle.pack(pady=(0, 25))

        # --- Карточка 1: Ссылка ---
        self.card_url = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=15)
        self.card_url.pack(fill="x", padx=40, pady=10)

        self.label_url = ctk.CTkLabel(self.card_url, text="Ссылка на видео", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_COLOR)
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

        self.label_path = ctk.CTkLabel(self.card_path, text="Папка для сохранения", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_COLOR)
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
            font=ctk.CTkFont(size=12), text_color=SUBTEXT_COLOR
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
