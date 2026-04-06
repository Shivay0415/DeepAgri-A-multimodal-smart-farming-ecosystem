from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen


GEOCODE_ENDPOINT = "https://api.openweathermap.org/geo/1.0/direct"
CURRENT_WEATHER_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"


class WeatherLookupError(Exception):
    pass


def get_openweather_api_key() -> str | None:
    return os.environ.get("OPENWEATHER_API_KEY") or os.environ.get("OPENWEATHERMAP_API_KEY")


def _fetch_json(base_url: str, params: dict[str, Any]) -> Any:
    url = base_url + "?" + urlencode(params)
    try:
        with urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise WeatherLookupError("OpenWeatherMap request failed.") from exc


def fetch_live_weather(location: str) -> dict:
    api_key = get_openweather_api_key()
    if not api_key:
        raise WeatherLookupError(
            "OPENWEATHER_API_KEY is not configured, so live weather lookup is unavailable."
        )

    locations = _fetch_json(
        GEOCODE_ENDPOINT,
        {
            "q": location,
            "limit": 1,
            "appid": api_key,
        },
    )
    if not locations:
        raise WeatherLookupError(f"Could not resolve location '{location}'.")

    resolved = locations[0]
    weather = _fetch_json(
        CURRENT_WEATHER_ENDPOINT,
        {
            "lat": resolved["lat"],
            "lon": resolved["lon"],
            "appid": api_key,
            "units": "metric",
        },
    )

    rain = weather.get("rain", {})
    observed_rain_mm = float(rain.get("1h") or rain.get("3h") or 0.0)

    weather_list = weather.get("weather") or []
    weather_info = weather_list[0] if weather_list else {}

    return {
        "source": "OpenWeatherMap current weather",
        "location_label": weather.get("name") or location,
        "latitude": resolved["lat"],
        "longitude": resolved["lon"],
        "temperature_c": float(weather["main"]["temp"]),
        "humidity_pct": float(weather["main"]["humidity"]),
        "observed_rain_mm": observed_rain_mm,
        "condition": weather_info.get("description", "unknown"),
        "wind_speed_mps": float(weather.get("wind", {}).get("speed") or 0.0),
    }
