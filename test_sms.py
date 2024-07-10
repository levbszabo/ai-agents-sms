import os
import requests
import json

product_description = """
Refer to the sample SMS
"""

# Get the API key from environment variables
API_KEY = os.getenv("SMS_API_KEY")


def test_generate_initial_sms(product_description, agent_id, local=True):
    if local:
        url = "http://127.0.0.1:8000/sms/generate-initial-sms"
    else:
        url = "https://api.journeymanai.io/sms/generate-initial-sms"
    payloads = {"product_description": product_description, "agent_id": agent_id}
    headers = {
        "Content-Type": "application/json",
        "JourneymanAI-SMS-API-Key": API_KEY,  # Add the API key to the headers
    }
    response = requests.post(url, json=payloads, headers=headers)
    out = json.loads(response.text)
    print("SMS Copy Generated")
    print(out)
    return out


def test_send_initial_sms(
    phone_number, initial_text, product_description, agent_id, local=True
):
    if local:
        url = "http://127.0.0.1:8000/sms/send-initial-sms"
    else:
        url = "https://api.journeymanai.io/sms/send-initial-sms"
    payloads = {
        "phone_number": phone_number,
        "initial_text": initial_text,
        "product_description": product_description,
        "agent_id": agent_id,
    }
    headers = {
        "Content-Type": "application/json",
        "JourneymanAI-SMS-API-Key": API_KEY,  # Add the API key to the headers
    }
    response = requests.post(url, json=payloads, headers=headers)
    out = json.loads(response.text)
    print("SMS Copy Generated")
    print(out)
    return out


# API V2 TEST SMS - GENERATE INITIAL TEXT
out = test_generate_initial_sms(product_description, 5, local=False)
initial_text = out.get("initial_text")
print(initial_text)

# API V2 TEST SEND INITIAL SMS
initial_text_filled = initial_text.format(first_name="Levi", business_type="finance")
phone_number = os.getenv("PERSONAL_PHONE_NUMBER")
out = test_send_initial_sms(
    phone_number, initial_text_filled, product_description, 5, local=False
)
print(out)
assert out["message_sid"]
