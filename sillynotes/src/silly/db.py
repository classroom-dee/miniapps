from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from .models import Message, Settings
from .settings import (
    DEFAULT_ROTATION_INTERVAL_SECONDS,
    MAX_ROTATION_INTERVAL_SECONDS,
    MIN_ROTATION_INTERVAL_SECONDS,
)


class Database:
    """Small SQLite wrapper

    Design choices for efficiency:
    - one connection reused for the app lifetime
    - WAL mode for resilient reads/writes
    - simple schema, no heavy ORM
    - indexed blacklist column for fast filtering
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self._initialize()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _initialize(self) -> None:
        with self.conn:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL UNIQUE,
                    is_blacklisted INTEGER NOT NULL DEFAULT 0 CHECK (is_blacklisted IN (0, 1)),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_messages_blacklisted
                ON messages (is_blacklisted);

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            self.conn.execute(
                """
                INSERT INTO settings(key, value)
                VALUES('rotation_interval_seconds', ?)
                ON CONFLICT(key) DO NOTHING
                """,
                (str(DEFAULT_ROTATION_INTERVAL_SECONDS),),
            )

    def add_message(self, text: str) -> int:
        normalized = self._normalize_message(text)
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO messages(text) VALUES (?)",
                (normalized,),
            )
        return int(cursor.lastrowid)

    def add_messages(self, texts: Iterable[str]) -> list[int]:
        ids: list[int] = []
        for text in texts:
            ids.append(self.add_message(text))
        return ids

    def delete_message(self, message_id: int) -> bool:
        with self.conn:
            cursor = self.conn.execute(
                "DELETE FROM messages WHERE id = ?",
                (message_id,),
            )
        return cursor.rowcount > 0

    def list_messages(self, include_blacklisted: bool = True) -> list[Message]:
        if include_blacklisted:
            cursor = self.conn.execute(
                "SELECT id, text, is_blacklisted, created_at FROM messages ORDER BY id ASC"
            )
        else:
            cursor = self.conn.execute(
                """
                SELECT id, text, is_blacklisted, created_at
                FROM messages
                WHERE is_blacklisted = 0
                ORDER BY id ASC
                """
            )
        return [self._row_to_message(row) for row in cursor.fetchall()]

    def get_message(self, message_id: int) -> Message | None:
        cursor = self.conn.execute(
            "SELECT id, text, is_blacklisted, created_at FROM messages WHERE id = ?",
            (message_id,),
        )
        row = cursor.fetchone()
        return self._row_to_message(row) if row else None

    def set_blacklist(self, message_id: int, is_blacklisted: bool) -> bool:
        with self.conn:
            cursor = self.conn.execute(
                "UPDATE messages SET is_blacklisted = ? WHERE id = ?",
                (1 if is_blacklisted else 0, message_id),
            )
        return cursor.rowcount > 0

    def get_next_message(self, last_message_id: int | None = None) -> Message | None:
        if last_message_id is None:
            cursor = self.conn.execute(
                """
                SELECT id, text, is_blacklisted, created_at
                FROM messages
                WHERE is_blacklisted = 0
                ORDER BY id ASC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            return self._row_to_message(row) if row else None

        cursor = self.conn.execute(
            """
            SELECT id, text, is_blacklisted, created_at
            FROM messages
            WHERE is_blacklisted = 0 AND id > ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (last_message_id,),
        )
        row = cursor.fetchone()
        if row:
            return self._row_to_message(row)

        cursor = self.conn.execute(
            """
            SELECT id, text, is_blacklisted, created_at
            FROM messages
            WHERE is_blacklisted = 0
            ORDER BY id ASC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        return self._row_to_message(row) if row else None

    def get_settings(self) -> Settings:
        cursor = self.conn.execute(
            "SELECT value FROM settings WHERE key = 'rotation_interval_seconds'"
        )
        row = cursor.fetchone()
        interval = int(row["value"]) if row else DEFAULT_ROTATION_INTERVAL_SECONDS
        return Settings(rotation_interval_seconds=interval)

    def set_rotation_interval(self, seconds: int) -> int:
        validated = self._validate_interval(seconds)
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO settings(key, value)
                VALUES('rotation_interval_seconds', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (str(validated),),
            )
        return validated

    @staticmethod
    def _normalize_message(text: str) -> str:
        normalized = " ".join(text.strip().split())
        if not normalized:
            raise ValueError("Message cannot be empty.")
        return normalized

    @staticmethod
    def _validate_interval(seconds: int) -> int:
        if not isinstance(seconds, int):
            raise TypeError("Interval must be an integer number of seconds.")
        if not (
            MIN_ROTATION_INTERVAL_SECONDS <= seconds <= MAX_ROTATION_INTERVAL_SECONDS
        ):
            raise ValueError(
                f"Interval must be between {MIN_ROTATION_INTERVAL_SECONDS} and {MAX_ROTATION_INTERVAL_SECONDS} seconds."
            )
        return seconds

    @staticmethod
    def _row_to_message(row: sqlite3.Row) -> Message:
        return Message(
            id=int(row["id"]),
            text=str(row["text"]),
            is_blacklisted=bool(row["is_blacklisted"]),
            created_at=str(row["created_at"]),
        )
