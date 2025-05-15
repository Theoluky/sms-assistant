#!/usr/bin/env python3
import sys
import requests
import uuid
import datetime

# === CONFIGURE THIS ===
# Your Render-deployed webhook endpoint:
URL = "https://sms-assistant-90xc.onrender.com/sms"
# Your test sender number (must be in AUTHORIZED_NUMBERS in your app)
TEST_FROM_NUMBER = "+18578698297"
# ======================

def build_payload(message_text: str) -> dict:
    """Construct a Telnyx-like webhook JSON with the given message_text."""
    return {
        "data": {
            "event_type": "message.received",
            "id": str(uuid.uuid4()),
            "occurred_at": datetime.datetime.utcnow().isoformat() + "+00:00",
            "payload": {
                "from": {
                    "carrier": "T-Mobile USA",
                    "line_type": "Wireless",
                    "phone_number": TEST_FROM_NUMBER
                },
                "text": message_text,
                # other fields can be added if needed
            },
            "record_type": "event"
        },
        "meta": {
            "attempt": 1,
            "delivered_to": URL
        }
    }

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} \"message here\"")
        sys.exit(1)

    # Join all args as the message
    message = " ".join(sys.argv[1:])
    payload = build_payload(message)

    try:
        resp = requests.post(URL, json=payload)
        print(f"POST {URL} → {resp.status_code}")
        print(resp.text)
    except Exception as e:
        print(f"Error sending request: {e}")

if __name__ == "__main__":
    main()



# Example data from Telnyx:
# {'data': {'event_type': 'message.received', 'id': '5ed9ec04-a33f-4ef2-b452-3a2989fac327', 'occurred_at': '2025-05-15T18:47:41.038+00:00', 'payload': {'autoresponse_type': None, 'cc': [], 'completed_at': None, 'cost': {'amount': '0.0160', 'currency': 'USD'}, 'cost_breakdown': {'carrier_fee': {'amount': '0.01200', 'currency': 'USD'}, 'rate': {'amount': '0.00400', 'currency': 'USD'}}, 'direction': 'inbound', 'encoding': 'GSM-7', 'errors': [], 'from': {'carrier': 'T-Mobile USA', 'line_type': 'Wireless', 'phone_number': '+18578698297'}, 'id': '1fa55452-5cc6-4ce7-9cb0-8612fa4ddc15', 'is_spam': False, 'media': [], 'messaging_profile_id': '400196d4-e32b-42c2-9654-190ffd5d9fb7', 'organization_id': 'ada11ebf-7c78-4f9d-914b-001da12f72d2', 'parts': 1, 'received_at': '2025-05-15T18:47:40.731+00:00', 'record_type': 'message', 'sent_at': None, 'subject': '', 'tags': [], 'text': 'Test for full JSON', 'to': [{'carrier': 'Telnyx', 'line_type': 'Wireless', 'phone_number': '+17179379708', 'status': 'webhook_delivered'}], 'type': 'SMS', 'valid_until': None, 'webhook_failover_url': None, 'webhook_url': 'https://sms-assistant-90xc.onrender.com/sms'}, 'record_type': 'event'}, 'meta': {'attempt': 1, 'delivered_to': 'https://sms-assistant-90xc.onrender.com/sms'}}