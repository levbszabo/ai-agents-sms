import os
import requests
import json

product_description = """
Refer to the sample SMS
"""


def test_generate_initial_sms(product_description, agent_id, local=True):
    if local:
        url = "http://127.0.0.1:8000/generate-initial-sms"
    else:
        url = "http://54.243.16.221/generate-initial-sms"
    payloads = {"product_description": product_description, "agent_id": agent_id}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payloads, headers=headers)
    out = json.loads(response.text)
    print("SMS Copy Generated")
    print(out)
    return out


def test_send_initial_sms(
    phone_number, initial_text, product_description, agent_id, local=True
):
    if local:
        url = "http://127.0.0.1:8000/send-initial-sms"
    else:
        url = "http://54.243.16.221/send-initial-sms"
    payloads = {
        "phone_number": phone_number,
        "initial_text": initial_text,
        "product_description": product_description,
        "agent_id": agent_id,
    }
    headers = {"Content-Type": "application/json"}
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
initial_text_filled = initial_text.format(first_name="Levi")
phone_number = os.getenv("PERSONAL_PHONE_NUMBER")
out = test_send_initial_sms(
    phone_number, initial_text_filled, product_description, 5, local=False
)
print(out)
assert out["message_sid"]

# API V2 TEST SMS RESPONSE
# Simply respond to the SMS directly and ensure 200 response
