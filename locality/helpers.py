# ---------------------------
# Weather helpers (Open-Meteo)
# ---------------------------

import sys
import os

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
    return os.path.join(icon_dir, file_name)


def fetch_current_weather(lat, lon, tz, icon_dir):
    """
    Returns (weather_icon, temperature_c) using Open-Meteo. May raise requests exceptions.
    """
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current_weather=true&timezone={tz}"
    )
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    data = r.json()
    cw = data.get("current_weather", {})
    code = cw.get("weathercode")
    temp = cw.get("temperature")
    icon = get_full_icon_path(code, icon_dir)  # must return full path
    return icon, temp


def geocode_city(name):
    """
    Use Open-Meteo geocoding to resolve city -> (name_display, lat, lon, timezone)
    Returns dict or None if not found.
    """
    url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        f"name={requests.utils.requote_uri(name)}&count=1&language=en&format=json"
    )
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    data = r.json()
    results = data.get("results") or []
    if not results:
        print(f"no result ! data: {data}")
        return None
    it = results[0]
    display = it["name"]
    if it.get("country"):
        display += f", {it['country']}"
    tz = it.get("timezone")
    return {"name": display, "lat": it["latitude"], "lon": it["longitude"], "tz": tz}
