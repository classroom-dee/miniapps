from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from silly.db import Database
from silly.models import Message


class NoteWidgetApp:
    def __init__(self, db_path: str | Path):
        self.db = Database(db_path)
        self.current_message_id: int | None = None
        self._rotation_job: str | None = None

        self.root = tk.Tk()
        self.root.title("Notes")
        self.root.geometry("320x120")
        self.root.minsize(260, 100)
        self.root.attributes("-topmost", True)

        self.message_var = tk.StringVar(value="No notes yet.")
        self.interval_var = tk.StringVar()

        self._build_main_ui()
        self._refresh_interval_label()
        self._show_initial_message()
        self._schedule_next_rotation()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_main_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill="both", expand=True)

        label = ttk.Label(
            outer,
            textvariable=self.message_var,
            anchor="center",
            justify="center",
            wraplength=280,
            font=("TkDefaultFont", 12),
        )
        label.pack(fill="both", expand=True, pady=(0, 8))

        controls = ttk.Frame(outer)
        controls.pack(fill="x")

        ttk.Button(controls, text="Next", command=self.rotate_now).pack(side="left")
        ttk.Button(controls, text="Manage", command=self.open_manager).pack(
            side="left", padx=(6, 0)
        )
        ttk.Label(controls, textvariable=self.interval_var).pack(side="right")

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

    def open_manager(self) -> None:
        ManagerWindow(self)

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
        self.window.geometry("520x360")
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
        self.tree = ttk.Treeview(
            self.window, columns=columns, show="headings", height=12
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("text", text="Message")
        self.tree.heading("blacklisted", text="Blacklisted")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("text", width=360, anchor="w")
        self.tree.column("blacklisted", width=90, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        interval = self.db.get_settings().rotation_interval_seconds
        self.interval_entry.delete(0, tk.END)
        self.interval_entry.insert(0, str(interval))

    def refresh_messages(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        messages = self.db.list_messages(include_blacklisted=True)
        for msg in messages:
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

        message_id = int(selection[0])
        return self.db.get_message(message_id)

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
