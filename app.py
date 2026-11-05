import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import os
import sys

# ================== НАСТРОЙКИ ПУТЕЙ ==================
if getattr(sys, 'frozen', False):
    # Если запущено как собранный .exe (PyInstaller распаковывает всё в _MEIPASS)
    BASE_DIR = sys._MEIPASS
    # Папка, куда сохранять видео (рядом с .exe)
    OUTPUT_DIR = os.path.dirname(sys.executable)
else:
    # Если запущено как .py скрипт
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = BASE_DIR

YTDLP_PATH = os.path.join(BASE_DIR, "yt-dlp.exe")

# ================== ТЕМА ==================
ctk.set_appearance_mode("dark")  # Тёмная тема
ctk.set_default_color_theme("blue")  # Синий акцент

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Video Downloader")
        self.geometry("900x750")
        self.minsize(800, 600)

        # --- Заголовок ---
        self.header = ctk.CTkLabel(
            self, text="📥 Video Downloader", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.header.pack(pady=(20, 10))

        self.subtitle = ctk.CTkLabel(
            self, text="Скачивайте видео с YouTube, Twitch и TikTok в один клик",
            font=ctk.CTkFont(size=13), text_color="gray"
        )
        self.subtitle.pack(pady=(0, 20))

        # --- Фрейм для ссылки ---
        self.frame_url = ctk.CTkFrame(self)
        self.frame_url.pack(fill="x", padx=30, pady=5)

        self.label_url = ctk.CTkLabel(self.frame_url, text="Ссылка на видео:", font=ctk.CTkFont(size=13, weight="bold"))
        self.label_url.pack(anchor="w", padx=15, pady=(10, 2))

        self.entry_url = ctk.CTkEntry(
            self.frame_url, placeholder_text="https://www.youtube.com/watch?v=...",
            height=40, font=ctk.CTkFont(size=13)
        )
        self.entry_url.pack(fill="x", padx=15, pady=(0, 15))

        # --- Фрейм для времени ---
        self.frame_time = ctk.CTkFrame(self)
        self.frame_time.pack(fill="x", padx=30, pady=5)

        self.label_time = ctk.CTkLabel(self.frame_time, text="Отрезок (необязательно, формат ЧЧ:ММ:СС):", font=ctk.CTkFont(size=13, weight="bold"))
        self.label_time.pack(anchor="w", padx=15, pady=(10, 2))

        self.time_inner = ctk.CTkFrame(self.frame_time, fg_color="transparent")
        self.time_inner.pack(fill="x", padx=15, pady=(0, 15))

        self.label_start = ctk.CTkLabel(self.time_inner, text="С:", font=ctk.CTkFont(size=13))
        self.label_start.pack(side="left", padx=(0, 5))

        self.entry_start = ctk.CTkEntry(self.time_inner, width=100, height=35, placeholder_text="00:00:00")
        self.entry_start.pack(side="left", padx=(0, 20))

        self.label_end = ctk.CTkLabel(self.time_inner, text="По:", font=ctk.CTkFont(size=13))
        self.label_end.pack(side="left", padx=(0, 5))

        self.entry_end = ctk.CTkEntry(self.time_inner, width=100, height=35, placeholder_text="00:00:00")
        self.entry_end.pack(side="left")

        # --- Кнопка ---
        self.btn_download = ctk.CTkButton(
            self, text="Скачать", height=45, 
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.start_download
        )
        self.btn_download.pack(fill="x", padx=30, pady=20)

        # --- Лог ---
        self.label_log = ctk.CTkLabel(self, text="Лог выполнения:", font=ctk.CTkFont(size=13, weight="bold"))
        self.label_log.pack(anchor="w", padx=30)

        self.log_text = ctk.CTkTextbox(
            self, height=300, font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#1a1a1a", text_color="#a6e3a1"
        )
        self.log_text.pack(fill="both", expand=True, padx=30, pady=(5, 20))

    def get_download_args(self, url, start_time, end_time):
        url_lower = url.lower()
        args = ["-S", "vcodec:h264,res,acodec:m4a", "--merge-output-format", "mp4", "-N", "16"]

        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            folder = os.path.join(OUTPUT_DIR, "youtube")
            args.extend(["--extractor-args", "youtube:player-client=default,-tv_simply"])
        elif "twitch.tv" in url_lower:
            folder = os.path.join(OUTPUT_DIR, "Twitch")
        elif "tiktok.com" in url_lower:
            folder = os.path.join(OUTPUT_DIR, "TikTok")
        else:
            folder = os.path.join(OUTPUT_DIR, "other")

        if start_time and end_time:
            args.extend(["--download-sections", f"*{start_time}-{end_time}"])
            filename_template = os.path.join(folder, f"%(title)s [{start_time.replace(':','_')}-{end_time.replace(':','_')}].%(ext)s")
        else:
            filename_template = os.path.join(folder, "%(title)s.%(ext)s")

        args.extend(["-o", filename_template])
        args.append(url.strip())
        return args, folder

    def download_thread(self, url, start_time, end_time):
        if not os.path.exists(YTDLP_PATH):
            self.log(f"❌ Ошибка: yt-dlp.exe не найден по пути {YTDLP_PATH}\n")
            return

        args, folder = self.get_download_args(url, start_time, end_time)
        os.makedirs(folder, exist_ok=True)
        cmd = [YTDLP_PATH] + args

        self.log(f"\n▶ Скачиваю: {url}\n")
        if start_time and end_time:
            self.log(f"  Отрезок: {start_time} - {end_time}\n")
        self.log(f"  Папка: {folder}\n")

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in process.stdout:
                self.log(line)
            process.wait()

            if process.returncode == 0:
                self.log(f"✅ Готово!\n")
            else:
                self.log(f"❌ Ошибка (код {process.returncode})\n")
        except Exception as e:
            self.log(f"❌ Ошибка запуска: {e}\n")

    def log(self, text):
        self.log_text.insert("end", text)
        self.log_text.see("end")

    def start_download(self):
        url = self.entry_url.get().strip()
        start_time = self.entry_start.get().strip()
        end_time = self.entry_end.get().strip()

        if not url:
            messagebox.showwarning("Внимание", "Вставьте ссылку на видео!")
            return
        if (start_time and not end_time) or (not start_time and end_time):
            messagebox.showwarning("Внимание", "Для отрезка укажите и начало, и конец (формат ЧЧ:ММ:СС).")
            return

        self.log_text.delete("1.0", "end")
        self.btn_download.configure(state="disabled", text="Скачиваю...")

        thread = threading.Thread(target=self.download_wrapper, args=(url, start_time, end_time))
        thread.daemon = True
        thread.start()

    def download_wrapper(self, url, start_time, end_time):
        self.download_thread(url, start_time, end_time)
        self.btn_download.configure(state="normal", text="Скачать")

if __name__ == "__main__":
    app = App()
    app.mainloop()
