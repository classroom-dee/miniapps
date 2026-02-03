# ---------------------------
# Weather helpers (Open-Meteo)
# ---------------------------

import sys
import os
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("This app needs 'requests'. Install with: pip install requests")
    sys.exit(1)

# Map Open-Meteo weathercode to icon
WEATHER_ICON = {
    0: "clear-day",
    1: "partly-cloudy-day",
    2: "partly-cloudy-day",
    3: "cloudy",
    45: "fog",
    48: "fog",
    51: "partly-cloudy-day-rain",
    53: "partly-cloudy-day-rain",
    55: "partly-cloudy-day-rain",
    56: "drizzle",
    57: "drizzle",
    61: "rain",
    63: "rain",
    65: "rain",
    66: "rain",
    67: "rain",
    71: "snow",
    73: "snow",
    75: "snow",
    77: "snow",
    80: "rain",
    81: "rain",
    82: "rain",
    85: "snow",
    86: "snow",
    95: "thunderstorm",
    96: "hail",
    99: "hail",
}


def get_full_icon_path(weather_code, icon_dir, extension=".png"):
    file_name = WEATHER_ICON.get(weather_code, "barometer")
    file_name += extension
    full_path = os.path.join(icon_dir, file_name)
    # log(f"INFO: icon full path: {full_path}")
    return full_path


def fetch_current_weather(lat, lon, tz, icon_dir, cache=None):
    """
    Returns (weather_icon, temperature_c) using Open-Meteo. May raise requests exceptions.
    """
    key = f"{lat},{lon}"

    if cache and key in cache:
        ts, icon, temp = cache[key]
        if datetime.now() - ts < timedelta(minutes=10):
            return icon, temp

    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current_weather=true&timezone={tz}"
    )

    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        data = r.json()
        cw = data.get("current_weather", {})

        icon = get_full_icon_path(
            cw.get("weathercode"), icon_dir
        )  # must return full path
        temp = cw.get("temperature")

        if cache is not None:
            cache[key] = (datetime.now(), icon, temp)

        return icon, temp

    except Exception as e:
        log(f"Something went wrong: {e}")
        return


def geocode_city(name):
    """
    Use Open-Meteo geocoding to resolve city -> (name_display, lat, lon, timezone)
    Returns dict or None if not found.
    """
    url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        f"name={requests.utils.requote_uri(name)}&count=1&language=en&format=json"
    )
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        data = r.json()
        results = data.get("results") or []
        if not results:
            return None
        it = results[0]
        display = it["name"]
        if it.get("country"):
            display += f", {it['country']}"
        tz = it.get("timezone")
        return {
            "name": display,
            "lat": it["latitude"],
            "lon": it["longitude"],
            "tz": tz,
        }
    except Exception as e:
        log(f"Something went wrong: {e}")
        return


LOG_FILE = "locale-master.log"


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
