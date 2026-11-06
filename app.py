import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import threading
import os
import sys
import re
import ctypes

# ================== НАСТРОЙКИ ПУТЕЙ ==================
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

YTDLP_PATH = os.path.join(BASE_DIR, "yt-dlp.exe")

# ================== ЗАГРУЗКА ШРИФТОВ (WINDOWS API) ==================
FALLBACK_FONT = "Segoe UI"
FONT_HEADER = FALLBACK_FONT
FONT_TEXT = FALLBACK_FONT

def load_fonts_windows():
    global FONT_HEADER, FONT_TEXT
    
    fonts_to_load = {
        "resotyg": ["ResotYgPERSONALUSE.otf", "ResotYgPERSONALUSE.ttf"],
        "threat": ["Threat.otf", "threat.otf", "Threat.ttf"]
    }
    
    # Флаг для Windows (FR_PRIVATE = 0x10, FR_NOT_ENUM = 0x20)
    FR_PRIVATE = 0x10 
    
    for name, files in fonts_to_load.items():
        for f in files:
            path = os.path.join(BASE_DIR, f)
            if os.path.exists(path):
                try:
                    # Загружаем шрифт напрямую в память Windows
                    result = ctypes.windll.gdi32.AddFontResourceExW(path, FR_PRIVATE, 0)
                    if result > 0:
                        if name == "resotyg":
                            FONT_HEADER = name
                        elif name == "threat":
                            FONT_TEXT = name
                        print(f"Успешно загружен шрифт: {f}")
                        break # Переходим к следующему шрифту
                    else:
                        print(f"Не удалось загрузить шрифт через API: {f}")
                except Exception as e:
                    print(f"Ошибка при загрузке шрифта {f}: {e}")
            else:
                print(f"Файл шрифта не найден: {path}")

# Вызываем функцию загрузки
load_fonts_windows()
