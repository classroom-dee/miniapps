from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Message:
    id: int
    text: str
    is_blacklisted: bool
    created_at: str


@dataclass(slots=True, frozen=True)
class Settings:
    rotation_interval_seconds: int
