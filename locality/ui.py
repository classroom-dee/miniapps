# ---------------------------
# UI
# ---------------------------

import sys
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import tkinter as tk
from tkinter import simpledialog, messagebox

from config import save_config, get_asset_path
from helpers import fetch_current_weather, geocode_city


class Row(tk.Frame):
    def __init__(self, master, city, font, cfg: dict, *args, **kwargs):
        super().__init__(master, bg="#111111", *args, **kwargs)
        self.cfg = cfg
        self.cfg.setdefault("weather_cache", {})
        self.city = city
        self.font = font
        self.fetching = False
        self.icon_img = None
        self.icon_dir = cfg["icon_path"]
        left = tk.Frame(self, bg="#111111")
        right = tk.Frame(self, bg="#111111")
        self.name_lbl = tk.Label(self, text="", font=font, fg="#eaeaea", bg="#111111")
        self.temp_lbl = tk.Label(self, text="", font=font, fg="#bdbdbd", bg="#111111")
        self.icon_lbl = tk.Label(self, fg="#eaeaea", bg="#111111")
        self.time_lbl = tk.Label(self, text="", font=font, fg="#eaeaea", bg="#111111")

        left.pack(side="left", fill="x", expand=True)
        right.pack(side="right")

        self.name_lbl.pack(in_=left, side="left", padx=(8, 6))

        self.temp_lbl.pack(in_=right, side="left", padx=(0, 6))
        self.icon_lbl.pack(in_=right, side="left", padx=(0, 6))
        self.time_lbl.pack(in_=right, side="left", padx=(0, 8))

        self.weather_icon = "…"
        self.temperature = None
        self.last_weather_fetch = datetime.min

    def update_time(self, use_24h=True):
        now = datetime.now(ZoneInfo(self.city["tz"]))
        fmt = "%Y-%m-%d %H:%M" if use_24h else "%Y-%m-%d %I-%M %p"
        self.name_lbl.config(text=self.city["name"])
        self.time_lbl.config(text=now.strftime(fmt))
        self.icon_lbl.config(image=self.icon_img)

        if self.temperature is None:
            self.temp_lbl.config(text="")
        else:
            self.temp_lbl.config(text=f"{round(self.temperature)}°C")

    def maybe_update_weather(
        self, min_interval=timedelta(minutes=10)
    ):  # runs on main thread
        if self.fetching:
            return
        if datetime.now() - self.last_weather_fetch < min_interval:
            return

        def worker():  # bg thread
            self.fetching = True

            result = fetch_current_weather(
                self.city["lat"],
                self.city["lon"],
                self.city["tz"],
                self.icon_dir,
                cache=self.cfg["weather_cache"],
            )
            if not result:
                self.after(0, lambda: setattr(self, "fetching", False))
                return
            
            icon, temp = result

            def apply():  # UI must be handled by main
                self.icon_img = tk.PhotoImage(file=icon)
                self.temperature = temp
                self.last_weather_fetch = datetime.now()
                self.fetching = False

            self.after(0, apply)  # scheduled to be on the tk main loop

            # # This runs UI job directly in the back -> cpu spike
            # try:
            #     icon, temp = fetch_current_weather(
            #         self.city["lat"], self.city["lon"], self.city["tz"], self.icon_dir
            #     )
            #     self.icon_img = tk.PhotoImage(file=icon)
            #     self.temperature = temp
            #     self.last_weather_fetch = datetime.now()
            # except Exception:
            #     # Leave previous icon/temp; try again later
            #     pass

        threading.Thread(target=worker, daemon=True).start()


class Widget(tk.Tk):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.cfg["icon_path"] = (
            get_asset_path()
        )  # do this at runtime, don't store it in config!!

        # Window setup
        self.overrideredirect(True)  # borderless
        self.configure(bg="#111111")
        self.attributes("-topmost", bool(cfg["window"].get("topmost", True)))
        x = cfg["window"].get("x", 100)
        y = cfg["window"].get("y", 100)
        self.geometry(f"+{x}+{y}")

        # Dragging
        self._drag_start = (0, 0)
        for bind_target in (self,):
            bind_target.bind("<ButtonPress-1>", self._on_start)
            bind_target.bind("<B1-Motion>", self._on_drag)

        # Right-click menu
        self.menu = tk.Menu(self, tearoff=0, bg="#222222", fg="#eaeaea")
        self.menu.add_command(label="Add city…", command=self.add_city_dialog)
        self.menu.add_command(label="Remove city…", command=self.remove_city_dialog)
        self.menu.add_separator()
        self._topmost_var = tk.BooleanVar(value=self.attributes("-topmost"))
        self.menu.add_checkbutton(
            label="Always on top",
            onvalue=True,
            offvalue=False,
            variable=self._topmost_var,
            command=self.toggle_topmost,
        )
        self.menu.add_checkbutton(
            label="24h format",
            onvalue=True,
            offvalue=False,
            variable=tk.BooleanVar(value=cfg.get("format_24h", True)),
            command=self.toggle_24h,
        )
        self.menu.add_separator()
        self.menu.add_command(label="Quit", command=self.safe_quit)
        self.bind("<Button-3>", self._show_menu)  # right-click

        # Content
        self.container = tk.Frame(self, bg="#111111")
        self.container.pack(padx=6, pady=6)

        self.font = (
            ("UbuntuMono Nerd Font Mono", 11)
            if sys.platform.startswith("win")
            else ("Helvetica", 11)
        )

        self.rows = []
        self.build_rows()

        # Keyboard
        self.bind("<Escape>", lambda e: self.toggle_titlebar())
        self.titlebar_shown = False

        # Periodic update loops
        self.update_loop()

        # Save window pos on close
        self.protocol("WM_DELETE_WINDOW", self.safe_quit)

    def build_rows(self):
        # clear
        for r in self.rows:
            r.destroy()
        self.rows = []

        for city in self.cfg["cities"]:
            row = Row(self.container, city, self.font, self.cfg)
            row.pack(fill="x", pady=2)
            self.rows.append(row)

    def _on_start(self, event):
        self._drag_start = (
            event.x_root - self.winfo_x(),
            event.y_root - self.winfo_y(),
        )

    def _on_drag(self, event):
        x = event.x_root - self._drag_start[0]
        y = event.y_root - self._drag_start[1]
        self.geometry(f"+{x}+{y}")
        # save as we drag (lightweight)
        self.cfg["window"]["x"] = x
        self.cfg["window"]["y"] = y
        save_config(self.cfg)

    def _show_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def toggle_topmost(self):
        val = not self.attributes("-topmost")
        self.attributes("-topmost", val)
        self.cfg["window"]["topmost"] = bool(val)
        save_config(self.cfg)

    def toggle_24h(self):
        self.cfg["format_24h"] = not self.cfg.get("format_24h", True)
        save_config(self.cfg)

    def toggle_titlebar(self):
        # Helpful if you "lose" the widget — toggling can help you move/close it
        self.titlebar_shown = not self.titlebar_shown
        self.overrideredirect(not self.titlebar_shown)

    def safe_quit(self):
        # persist before exit
        pos = (self.winfo_x(), self.winfo_y())
        self.cfg["window"]["x"], self.cfg["window"]["y"] = pos
        save_config(self.cfg)
        self.destroy()

    def add_city_dialog(self):
        name = simpledialog.askstring(
            "Add city", "City name (e.g., Seoul, Tokyo, London):", parent=self
        )
        if not name:
            return
        try:
            result = geocode_city(name.strip())
            if not result:
                messagebox.showerror("Not found", f"Couldn't find: {name}")
                return
            self.cfg["cities"].append(result)
            save_config(self.cfg)
            self.build_rows()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add city:\n{e}")

    def remove_city_dialog(self):
        if not self.cfg["cities"]:
            messagebox.showinfo("Remove city", "No cities to remove.")
            return
        # Quick & dirty text prompt where the user types an index or name
        names = [c["name"] for c in self.cfg["cities"]]
        prompt = "Type a number to remove:\n" + "\n".join(
            f"{i + 1}. {n}" for i, n in enumerate(names)
        )
        val = simpledialog.askstring("Remove city", prompt, parent=self)
        if not val:
            return
        try:
            idx = int(val) - 1
            if 0 <= idx < len(self.cfg["cities"]):
                self.cfg["cities"].pop(idx)
                save_config(self.cfg)
                self.build_rows()
                return
        except ValueError:
            # Try by name
            pass
        # by name
        name = val.strip().lower()
        new_list = [c for c in self.cfg["cities"] if c["name"].lower() != name]
        if len(new_list) == len(self.cfg["cities"]):
            messagebox.showerror("Not found", f"No city removed: {val}")
            return
        self.cfg["cities"] = new_list
        save_config(self.cfg)
        self.build_rows()

    def update_loop(self):
        # Update times every 0.5s for snappy minutes transition
        for r in self.rows:
            r.update_time(use_24h=self.cfg.get("format_24h", True))
            r.maybe_update_weather(min_interval=timedelta(minutes=10))
        self.after(5000, self.update_loop)
