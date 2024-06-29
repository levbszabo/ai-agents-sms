import os
import requests
import json

product_description = """
**Recommendation Systems**
- Recommendation types: product, content
- Number of users/items: 1000-5000
- Data sources for recommendations?
- Real-time or batch recommendations?
- Integration with existing systems?

**Pricing**:
- Monthly Retainer: $3,500 - $6,000 (through project completion)
- Monthly Maintenance: $1,200 - $2,000 (after project completion)
- Usage Cost: $0.02 - $0.04 per recommendation
- Time Estimate: 6-10 weeks
Implementing a recommendation system can significantly boost customer
 engagement and sales by delivering personalized product or content
   suggestions, leading to higher conversion rates and increased 
   customer satisfaction. This tailored approach not only enhances 
   user experience but also drives repeat business and maximizes 
   lifetime customer value.
"""


def test_generate_initial_sms(product_description, agent_id, local=True):
    if local:
        url = 'http://127.0.0.1:8000/generate-initial-sms'
    else:
        url = 'XXX/generate-initial-sms'
    payloads = {
        "product_description": product_description,
        "agent_id": agent_id
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payloads, headers=headers)
    out = json.loads(response.text)
    print("SMS Copy Generated")
    print(out)
    return out


def test_send_initial_sms(phone_number, initial_text, product_description, agent_id, local=True):
    if local:
        url = 'http://127.0.0.1:8000/send-initial-sms'
    else:
        url = 'http://XXX/send-initial-sms'
    payloads = {
        "phone_number": phone_number,
        "initial_text": initial_text,
        "product_description": product_description,
        "agent_id": agent_id
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payloads, headers=headers)
    out = json.loads(response.text)
    print("SMS Copy Generated")
    print(out)
    return out


# API V2 TEST SMS - GENERATE INITIAL TEXT
out = test_generate_initial_sms(product_description, 2, local=True)
initial_text = out.get('initial_text')
print(initial_text)
assert initial_text
# API V2 TEST SEND INITIAL SMS
initial_text_filled = initial_text.format(
    first_name="Levi")
phone_number = os.getenv("PERSONAL_PHONE_NUMBER")
out = test_send_initial_sms(
    phone_number, initial_text_filled, product_description, 2, local=True)
print(out)
assert out['message_sid']

# API V2 TEST SMS RESPONSE
# Simply respond to the SMS directly and ensure 200 response
