from flask import Flask, request, Response
import requests
import os
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
        return "Weather data here..."
    elif text.startswith("search"):
        return "Search result here..."
    else:
        return "Sorry, I didn't understand. Try: weather <city> or search <query>."
    
def get_weather_data(location):
    """
    location: either "lat,lon" (e.g. "39.7392,-105.9903")
              or a simple place name for geocoding (e.g. "Denver,CO").
    """
    # 1. Parse latitude & longitude
    if "," in location:
        lat_str, lon_str = location.split(",", 1)
        lat, lon = lat_str.strip(), lon_str.strip()
    else:
        # For simplicity, use Open-Meteo's geocoding endpoint (no key)
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1}
        ).json()
        if not geo.get("results"):
            return f"Could not geocode '{location}'."
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]

    # 2. Get forecast URL from NWS
    pt = requests.get(f"https://api.weather.gov/points/{lat},{lon}")
    if pt.status_code != 200:
        return "Error contacting NWS."
    forecast_url = pt.json()["properties"]["forecast"]

    # 3. Fetch the forecast
    forecast = requests.get(forecast_url).json()
    periods = forecast.get("properties", {}).get("periods", [])
    if not periods:
        return "No forecast available."

    # 4. Build a short summary (today’s daytime and nighttime)
    today = []
    for p in periods[:2]:  # usually [0]=Today Day, [1]=Tonight
        name = p["name"]        # e.g. "Today", "Tonight"
        temp = p["temperature"] # numeric
        unit = p["temperatureUnit"]
        short = p["shortForecast"]  # e.g. "Partly Sunny"
        today.append(f"{name}: {short}, {temp}°{unit}")

    return " / ".join(today)

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