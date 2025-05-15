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
    # your existing logic...
    text = text.lower()
    if text.startswith("weather"):
        # e.g. "weather 39.7392,-105.9903" or "weather denver,co"
        parts = text.split(" ", 1)
        loc = parts[1] if len(parts) > 1 else ""
        if not loc:
            return "Usage: weather <lat,lon> or weather <City,State>"
        return get_weather_nws(loc)
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

def get_weather_nws(location, days=3):
    """
    Fetch a multi-day weather outlook from NOAA NWS.
    location: either "lat,lon" (e.g. "39.7392,-105.9903")
              or a place name (e.g. "Estes Park,CO", "Denver, CO")
    days: how many future days to include (default 3)
    """
    # 1. Determine if the input is numeric lat,lon
    m = LATLON_RE.match(location)
    if m:
        lat = m.group("lat")
        lon = m.group("lon")
    else:
        # Treat as place name → geocode via Open-Meteo
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1}
        ).json()
        if not geo.get("results"):
            return f"Could not find location '{location}'."
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]

    # 2. Ask NWS for the point metadata
    pt = requests.get(f"https://api.weather.gov/points/{lat},{lon}")
    if pt.status_code != 200:
        return "Error fetching location info from NWS."
    forecast_url = pt.json()["properties"]["forecast"]

    # 3. Fetch the forecast periods
    resp = requests.get(forecast_url)
    if resp.status_code != 200:
        return "Error fetching forecast from NWS."
    periods = resp.json().get("properties", {}).get("periods", [])
    if not periods:
        return "No forecast data available."

    # 4. Build outlook: day+night for the next `days` days
    outlook = []
    slice_end = min(len(periods), 2 * days)
    for p in periods[:slice_end]:
        name = p["name"]               # e.g. "Today", "Tonight", "Tuesday", ...
        temp = p["temperature"]        # integer
        unit = p["temperatureUnit"]    # e.g. "F"
        short = p["shortForecast"]     # e.g. "Partly Sunny"
        outlook.append(f"{name}: {short}, {temp}°{unit}")

    # 5. Join into one SMS-friendly string
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