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
    data = request.json
    from_number = data.get("from")
    body = data.get("text", "").strip()

    if from_number not in AUTHORIZED_NUMBERS:
        return Response(status=403)

    reply = handle_message(body)
    send_sms(from_number, reply)
    return Response(status=200)

def handle_message(text):
    return "You said: " + text

def send_sms(to, message):
    headers = {
        "Authorization": f"Bearer {TELNYX_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "from": "YOUR_TELNYX_NUMBER",  # replace this
        "to": to,
        "text": message,
        "messaging_profile_id": TELNYX_MESSAGING_PROFILE_ID
    }
    requests.post("https://api.telnyx.com/v2/messages", headers=headers, json=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)