import os
import requests
import json

product_description = """
Journeyman AI offers cutting-edge AI solutions designed to enhance business efficiency,
 drive sales, and improve customer engagement. Our services include AI Client Acquisition,
   automating lead qualification, quote generation, and appointment booking with 24/7
     availability and seamless calendar integration. Our Bridge AI tool streamlines client 
     communications and onboarding, making it ideal for relationship-focused businesses.
       Charisma AI enhances client satisfaction through sentiment analysis and segmentation,
         improving interactions. We provide both out-of-the-box and custom AI solutions
           tailored to your unique business needs, backed by expert engineering and data science.
             Discover how our AI implementations can unlock significant ROI and transform
               your business with scalable, data-driven insights.
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
out = test_generate_initial_sms(product_description, 2, local=False)
initial_text = out.get("initial_text")
print(initial_text)
assert initial_text
# API V2 TEST SEND INITIAL SMS
initial_text_filled = initial_text.format(first_name="Levi")
phone_number = os.getenv("PERSONAL_PHONE_NUMBER")
out = test_send_initial_sms(
    phone_number, initial_text_filled, product_description, 2, local=False
)
print(out)
assert out["message_sid"]

# API V2 TEST SMS RESPONSE
# Simply respond to the SMS directly and ensure 200 response
