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
    fulljson = request.json
    data = fulljson.get("data")
    from_number = data.get("from")
    body = data.get("text", "").strip()
    print(data)

    # if from_number not in AUTHORIZED_NUMBERS:
    #     return Response(status=403)

    reply = handle_message(body)
    # send_sms(from_number, reply)
    print(from_number, reply)
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


# Example data from Telnyx:
# {'data': {'event_type': 'message.received', 'id': '5ed9ec04-a33f-4ef2-b452-3a2989fac327', 'occurred_at': '2025-05-15T18:47:41.038+00:00', 'payload': {'autoresponse_type': None, 'cc': [], 'completed_at': None, 'cost': {'amount': '0.0160', 'currency': 'USD'}, 'cost_breakdown': {'carrier_fee': {'amount': '0.01200', 'currency': 'USD'}, 'rate': {'amount': '0.00400', 'currency': 'USD'}}, 'direction': 'inbound', 'encoding': 'GSM-7', 'errors': [], 'from': {'carrier': 'T-Mobile USA', 'line_type': 'Wireless', 'phone_number': '+18578698297'}, 'id': '1fa55452-5cc6-4ce7-9cb0-8612fa4ddc15', 'is_spam': False, 'media': [], 'messaging_profile_id': '400196d4-e32b-42c2-9654-190ffd5d9fb7', 'organization_id': 'ada11ebf-7c78-4f9d-914b-001da12f72d2', 'parts': 1, 'received_at': '2025-05-15T18:47:40.731+00:00', 'record_type': 'message', 'sent_at': None, 'subject': '', 'tags': [], 'text': 'Test for full JSON', 'to': [{'carrier': 'Telnyx', 'line_type': 'Wireless', 'phone_number': '+17179379708', 'status': 'webhook_delivered'}], 'type': 'SMS', 'valid_until': None, 'webhook_failover_url': None, 'webhook_url': 'https://sms-assistant-90xc.onrender.com/sms'}, 'record_type': 'event'}, 'meta': {'attempt': 1, 'delivered_to': 'https://sms-assistant-90xc.onrender.com/sms'}}