# ---------------------------
# Config / persistence
# ---------------------------

import os
import json
from pathlib import Path

APP_NAME = "locale_master"
CONFIG_PATH = Path(os.path.expanduser(f"~/.{APP_NAME}.json"))

DEFAULT_CITIES = [
    {"name": "Seoul", "lat": 37.5665, "lon": 126.9780, "tz": "Asia/Seoul"},
    {"name": "New York", "lat": 40.7128, "lon": -74.0060, "tz": "America/New_York"},
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "tz": "Asia/Tokyo"},
]


def get_asset_path():
    proj_path = Path(__file__).resolve().parent
    return os.path.join(os.path.join(proj_path, "assets"), "meteocon")


def load_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # default
    return {
        "window": {"x": 100, "y": 100, "topmost": True},
        "cities": DEFAULT_CITIES,
        "format_24h": True,
        "weather_cache": {},  # code->icon cache & per-city timestamps
        "icon_path": get_asset_path(),
    }


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Failed to save config:", e)
