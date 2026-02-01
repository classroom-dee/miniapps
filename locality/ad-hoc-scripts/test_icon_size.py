import tkinter as tk
from tkinter import font

r = tk.Tk()
r.withdraw()
f = font.Font(family="Segoe UI Emoji", size=14)
for ch in ["☀️", "🌤️", "⛅", "🌥️", "🌫️", "🌫️", "🌦️", "⛈️"]:
    print(ch, [hex(ord(c)) for c in ch])
