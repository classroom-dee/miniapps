from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from silly.db import Database
from silly.models import Message


class NoteWidgetApp:
    def __init__(self, db_path: str | Path):
        self.db = Database(db_path)
        self.current_message_id: int | None = None
        self._rotation_job: str | None = None
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self.is_pinned = True

        self.root = tk.Tk()
        self.root.title("Today's note")
        self.root.geometry("340x120+80+80")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", self.is_pinned)

        self.message_var = tk.StringVar(value="No active notes. Add one in Manage.")
        self.pin_var = tk.StringVar(value="Pinned")
        self.interval_var = tk.StringVar()

        self._build_main_ui()
        self._build_context_menu()
        self._bind_window_drag()
        self._refresh_interval_label()
        self._show_initial_message()
        self._schedule_next_rotation()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_main_ui(self) -> None:
        self.root.configure(bg="#202225")

        outer = tk.Frame(
            self.root,
            bg="#202225",
            highlightthickness=1,
            highlightbackground="#4a4f57",
            bd=0,
        )
        outer.pack(fill="both", expand=True)

        title_bar = tk.Frame(outer, bg="#2b2f36", height=26)
        title_bar.pack(fill="x")

        self.title_label = tk.Label(
            title_bar,
            text="Today's note",
            bg="#2b2f36",
            fg="#f2f2f2",
            anchor="w",
            padx=8,
        )
        self.title_label.pack(side="left", fill="x", expand=True)

        self.status_label = tk.Label(
            title_bar,
            textvariable=self.pin_var,
            bg="#2b2f36",
            fg="#c7c7c7",
            padx=6,
        )
        self.status_label.pack(side="right")

        body = tk.Frame(outer, bg="#202225", padx=10, pady=10)
        body.pack(fill="both", expand=True)

        self.message_label = tk.Label(
            body,
            textvariable=self.message_var,
            bg="#202225",
            fg="#ffffff",
            justify="center",
            wraplength=300,
            font=("TkDefaultFont", 11),
        )
        self.message_label.pack(fill="both", expand=True)

        footer = tk.Frame(body, bg="#202225")
        footer.pack(fill="x", pady=(8, 0))

        tk.Button(
            footer,
            text="Next",
            command=self.rotate_now,
            relief="flat",
            bd=0,
            padx=8,
            pady=3,
        ).pack(side="left")

        tk.Button(
            footer,
            text="Manage",
            command=self.open_manager,
            relief="flat",
            bd=0,
            padx=8,
            pady=3,
        ).pack(side="left", padx=(6, 0))

        tk.Label(
            footer,
            textvariable=self.interval_var,
            bg="#202225",
            fg="#bbbbbb",
        ).pack(side="right")

        self.message_label.bind("<Double-Button-1>", lambda _e: self.open_manager())
        self.root.bind("<Button-3>", self._show_context_menu)

    def _build_context_menu(self) -> None:
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Next note", command=self.rotate_now)
        self.menu.add_command(label="Manage notes", command=self.open_manager)
        self.menu.add_separator()
        self.menu.add_command(label="Pin / Unpin", command=self.toggle_pin)
        self.menu.add_command(label="Import Text File", command=self.import_messages)
        self.menu.add_separator()
        self.menu.add_command(label="Quit", command=self.on_close)

    def _show_context_menu(self, event: tk.Event) -> None:
        self.menu.tk_popup(event.x_root, event.y_root)

    def _bind_window_drag(self) -> None:
        drag_widgets = [self.root, self.title_label, self.status_label]
        for widget in drag_widgets:
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_offset_x = event.x_root - self.root.winfo_x()
        self._drag_offset_y = event.y_root - self.root.winfo_y()

    def _on_drag(self, event: tk.Event) -> None:
        x = event.x_root - self._drag_offset_x
        y = event.y_root - self._drag_offset_y
        self.root.geometry(f"+{x}+{y}")

    def _refresh_interval_label(self) -> None:
        settings = self.db.get_settings()
        self.interval_var.set(f"{settings.rotation_interval_seconds}s")

    def _show_initial_message(self) -> None:
        message = self.db.get_next_message()
        if message is None:
            self.current_message_id = None
            self.message_var.set("No active notes. Add one in Manage.")
            return

        self.current_message_id = message.id
        self.message_var.set(message.text)

    def _schedule_next_rotation(self) -> None:
        self._cancel_scheduled_rotation()
        interval_ms = self.db.get_settings().rotation_interval_seconds * 1000
        self._rotation_job = self.root.after(interval_ms, self._rotate_and_reschedule)

    def _cancel_scheduled_rotation(self) -> None:
        if self._rotation_job is not None:
            self.root.after_cancel(self._rotation_job)
            self._rotation_job = None

    def _rotate_and_reschedule(self) -> None:
        self.rotate_now()
        self._schedule_next_rotation()

    def rotate_now(self) -> None:
        message = self.db.get_next_message(self.current_message_id)
        if message is None:
            self.current_message_id = None
            self.message_var.set("No active notes. Add one in Manage.")
            return

        self.current_message_id = message.id
        self.message_var.set(message.text)

    def toggle_pin(self) -> None:
        self.is_pinned = not self.is_pinned
        self.root.attributes("-topmost", self.is_pinned)
        self.pin_var.set("Pinned" if self.is_pinned else "Unpinned")

    def open_manager(self) -> None:
        ManagerWindow(self)

    def import_messages(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Import notes from text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        added = 0
        skipped = 0

        try:
            with open(path, "r", encoding="utf-8") as handle:
                for line in handle:
                    text = line.strip()
                    if not text:
                        continue
                    try:
                        self.db.add_message(text)
                        added += 1
                    except Exception:
                        skipped += 1
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc), parent=self.root)
            return

        if self.current_message_id is None:
            self.rotate_now()
        self._schedule_next_rotation()

        messagebox.showinfo(
            "Import complete",
            f"Added: {added}\nSkipped: {skipped}",
            parent=self.root,
        )

    def on_close(self) -> None:
        self._cancel_scheduled_rotation()
        self.db.close()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


class ManagerWindow:
    def __init__(self, app: NoteWidgetApp):
        self.app = app
        self.db = app.db

        self.window = tk.Toplevel(app.root)
        self.window.title("Manage notes")
        self.window.geometry("560x380")
        self.window.transient(app.root)

        self._build_ui()
        self.refresh_messages()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.window, padding=10)
        outer.pack(fill="both", expand=True)

        top = ttk.Frame(outer)
        top.pack(fill="x", pady=(0, 8))

        ttk.Button(top, text="Add", command=self.add_message).pack(side="left")
        ttk.Button(top, text="Delete", command=self.delete_selected).pack(
            side="left", padx=(6, 0)
        )
        ttk.Button(
            top, text="Toggle Blacklist", command=self.toggle_blacklist_selected
        ).pack(side="left", padx=(6, 0))
        ttk.Button(top, text="Refresh", command=self.refresh_messages).pack(
            side="left", padx=(6, 0)
        )

        interval_frame = ttk.Frame(outer)
        interval_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(interval_frame, text="Rotation interval (seconds):").pack(side="left")
        self.interval_entry = ttk.Entry(interval_frame, width=10)
        self.interval_entry.pack(side="left", padx=(6, 6))
        ttk.Button(interval_frame, text="Save", command=self.save_interval).pack(
            side="left"
        )

        columns = ("id", "text", "blacklisted")
        self.tree = ttk.Treeview(outer, columns=columns, show="headings", height=14)
        self.tree.heading("id", text="ID")
        self.tree.heading("text", text="Message")
        self.tree.heading("blacklisted", text="Blacklisted")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("text", width=390, anchor="w")
        self.tree.column("blacklisted", width=90, anchor="center")
        self.tree.pack(fill="both", expand=True)

        interval = self.db.get_settings().rotation_interval_seconds
        self.interval_entry.delete(0, tk.END)
        self.interval_entry.insert(0, str(interval))

    def refresh_messages(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for msg in self.db.list_messages(include_blacklisted=True):
            self.tree.insert(
                "",
                "end",
                iid=str(msg.id),
                values=(msg.id, msg.text, "yes" if msg.is_blacklisted else "no"),
            )

    def add_message(self) -> None:
        text = simpledialog.askstring("Add note", "Enter the note:", parent=self.window)
        if text is None:
            return

        try:
            self.db.add_message(text)
        except Exception as exc:
            messagebox.showerror("Could not add note", str(exc), parent=self.window)
            return

        self.refresh_messages()
        if self.app.current_message_id is None:
            self.app.rotate_now()
        self.app._schedule_next_rotation()

    def _selected_message(self) -> Message | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return self.db.get_message(int(selection[0]))

    def delete_selected(self) -> None:
        message = self._selected_message()
        if message is None:
            messagebox.showinfo(
                "Delete note", "Select a note first.", parent=self.window
            )
            return

        self.db.delete_message(message.id)
        if self.app.current_message_id == message.id:
            self.app.current_message_id = None
            self.app.rotate_now()

        self.refresh_messages()
        self.app._schedule_next_rotation()

    def toggle_blacklist_selected(self) -> None:
        message = self._selected_message()
        if message is None:
            messagebox.showinfo(
                "Blacklist note", "Select a note first.", parent=self.window
            )
            return

        self.db.set_blacklist(message.id, not message.is_blacklisted)

        if self.app.current_message_id == message.id and not message.is_blacklisted:
            self.app.current_message_id = None
            self.app.rotate_now()

        self.refresh_messages()
        self.app._schedule_next_rotation()

    def save_interval(self) -> None:
        raw = self.interval_entry.get().strip()
        try:
            seconds = int(raw)
            self.db.set_rotation_interval(seconds)
        except Exception as exc:
            messagebox.showerror("Invalid interval", str(exc), parent=self.window)
            return

        self.app._refresh_interval_label()
        self.app._schedule_next_rotation()
        messagebox.showinfo("Saved", "Rotation interval updated.", parent=self.window)
