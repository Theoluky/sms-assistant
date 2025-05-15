from flask import Flask, request, Response
import requests
import os
import re
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

TELNYX_API_KEY = os.environ.get("TELNYX_API_KEY")
TELNYX_MESSAGING_PROFILE_ID = os.environ.get("TELNYX_MESSAGING_PROFILE_ID")
AUTHORIZED_NUMBERS = os.environ.get("AUTHORIZED_NUMBER")  # replace this

# print(TELNYX_API_KEY, TELNYX_MESSAGING_PROFILE_ID, AUTHORIZED_NUMBERS)


@app.route("/sms", methods=["POST"])
def receive_sms():
    data = request.get_json(force=True)
    app.logger.debug("Raw Telnyx JSON: %s", data)

    # Drill into the nested structure:
    event = data.get("data", {})
    payload = event.get("payload", {})

    # 'from' is itself an object with 'phone_number'
    from_info = payload.get("from", {})
    from_number = from_info.get("phone_number") 
    message_body = payload.get("text", "").strip()  # e.g. "Test for full JSON"

    # Basic validation
    if not from_number:
        app.logger.error("Missing 'from' phone_number in payload")
        return Response("Bad Request: no sender", status=400)

    if from_number not in AUTHORIZED_NUMBERS:
        app.logger.warning("Unauthorized sender: %s", from_number)
        return Response(status=403)

    # Now handle the message
    reply = handle_message(message_body)
    print(reply)
    # send_sms(from_number, reply)
    return Response(status=200)

def handle_message(text):
    text = text.strip()
    if text.lower().startswith("weather"):
        parts = text.split(" ", 1)
        if len(parts) < 2:
            return "Usage: weather <lat,lon> or weather <City,State>"
        return get_weather_nws(parts[1], days=3)
    elif text.startswith("search"):
        return "Search result here..."
    else:
        return "Sorry, I didn't understand. Try: weather <city> or search <query>."
    
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

def send_sms(to_number, body):
    url = "https://api.telnyx.com/v2/messages"
    headers = {
        "Authorization": f"Bearer {TELNYX_API_KEY}",
        "Content-Type": "application/json"
    }
    json_data = {
        "from": "YOUR_TELNYX_NUMBER",          # e.g. "+17179379708"
        "to": to_number,
        "text": body,
        "messaging_profile_id": TELNYX_MESSAGING_PROFILE_ID
    }
    resp = requests.post(url, headers=headers, json=json_data)
    app.logger.info("Sent SMS to %s: %s %s", to_number, resp.status_code, resp.text)

if __name__ == "__main__":
    # for local dev you might use app.run(debug=True)
    app.run(host="0.0.0.0", port=5000)

# Example data from Telnyx:
# {'data': {'event_type': 'message.received', 'id': '5ed9ec04-a33f-4ef2-b452-3a2989fac327', 'occurred_at': '2025-05-15T18:47:41.038+00:00', 'payload': {'autoresponse_type': None, 'cc': [], 'completed_at': None, 'cost': {'amount': '0.0160', 'currency': 'USD'}, 'cost_breakdown': {'carrier_fee': {'amount': '0.01200', 'currency': 'USD'}, 'rate': {'amount': '0.00400', 'currency': 'USD'}}, 'direction': 'inbound', 'encoding': 'GSM-7', 'errors': [], 'from': {'carrier': 'T-Mobile USA', 'line_type': 'Wireless', 'phone_number': '+18578698297'}, 'id': '1fa55452-5cc6-4ce7-9cb0-8612fa4ddc15', 'is_spam': False, 'media': [], 'messaging_profile_id': '400196d4-e32b-42c2-9654-190ffd5d9fb7', 'organization_id': 'ada11ebf-7c78-4f9d-914b-001da12f72d2', 'parts': 1, 'received_at': '2025-05-15T18:47:40.731+00:00', 'record_type': 'message', 'sent_at': None, 'subject': '', 'tags': [], 'text': 'Test for full JSON', 'to': [{'carrier': 'Telnyx', 'line_type': 'Wireless', 'phone_number': '+17179379708', 'status': 'webhook_delivered'}], 'type': 'SMS', 'valid_until': None, 'webhook_failover_url': None, 'webhook_url': 'https://sms-assistant-90xc.onrender.com/sms'}, 'record_type': 'event'}, 'meta': {'attempt': 1, 'delivered_to': 'https://sms-assistant-90xc.onrender.com/sms'}}