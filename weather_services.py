import re
import requests

# Pre-compile a regex for “lat,lon” detection
LATLON_RE = re.compile(r"""
    ^\s*                            # optional leading space
    (?P<lat>[-+]?\d+(\.\d+)?)       # latitude: integer or decimal
    \s*,\s*                         # comma separator (allow spaces)
    (?P<lon>[-+]?\d+(\.\d+)?)       # longitude: integer or decimal
    \s*$                            # optional trailing space
""", re.VERBOSE)

def geocode(location: str):
    """Return (lat, lon) for a place name or numeric pair, or (None, None)."""
    # A) If it's literally "lat,lon", parse it
    m = LATLON_RE.match(location)
    if m:
        return m.group("lat"), m.group("lon")

    # B) Try Open-Meteo geocoder
    try:
        resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1},
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("results"):
            r = data["results"][0]
            return r["latitude"], r["longitude"]
    except Exception:
        # silent fallback
        pass

    # C) Fallback to Nominatim (OpenStreetMap)
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": location, "format": "json", "limit": 1},
            headers={"User-Agent": "sms-weather-bot/1.0"},
            timeout=5
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            return results[0]["lat"], results[0]["lon"]
    except Exception:
        pass

    return None, None

def get_weather_nws(location: str, days: int = 3) -> str:
    """Fetch a multi-day forecast from NOAA NWS given a place name or lat,lon."""
    lat, lon = geocode(location)
    if not lat or not lon:
        return f"❌ Could not geocode '{location}'."

    # 2. Get forecast endpoint
    pt = requests.get(f"https://api.weather.gov/points/{lat},{lon}", timeout=5)
    if pt.status_code != 200:
        return "⚠️ NWS lookup failed."
    forecast_url = pt.json()["properties"]["forecast"]

    # 3. Fetch periods
    fx = requests.get(forecast_url, timeout=5)
    if fx.status_code != 200:
        return "⚠️ NWS forecast fetch failed."
    periods = fx.json().get("properties", {}).get("periods", [])
    if not periods:
        return "❌ No forecast data."

    # 4. Build the outlook
    outlook = []
    for p in periods[: 2 * days]:
        outlook.append(f"{p['name']}: {p['shortForecast']}, {p['temperature']}°{p['temperatureUnit']}")
    return " | ".join(outlook)