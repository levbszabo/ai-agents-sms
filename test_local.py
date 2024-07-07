# import the generate_initial_text and generate_text_response functions from main
# generate test code that is entirely loacal to test the functions in a controlled,
# conversational way
from main import generate_initial_text, get_agent, get_db, generate_text_response
from tools import CalendarBookingTool
from fixtures import SAMPLE_SMS as sample_sms

tools = [CalendarBookingTool()]
# Generate initial text
product_description = "Refer to the sample SMS"
agent_id = 5
initial_prompt = """
Write a short text message, in the voice of a friendly Sales Agent. The message should briefly summarize 
the important aspects of the product/service we are pitching, highlighting to the recipient why they may wish to implement 
the service. This text should come from Levente from Journeyman AI. Ensure that the placeholders are left open as in the sample

Ensure the length of the message is less than 250 characters.
Sample: {sample}

Product Description: {product_description}
"""
prompt = """
Write a short text message, in the voice of a friendly sales agent. The message should respond to the user's text message and move
the conversation forward. Use the conversation history as well as the product description to answer any questions the user ma
y have about the product. You are polite, direct, and keep your messages relatively brief. Be engaging, conversational, and
natural. Keep your messages brief but personable, aiming to build a connection with the user. Use a mix of casual language,
emojis, and questions to keep the conversation lively and interactive. Pay attention to emotional cues and respond appropriately 
to build rapport and guide the user toward a purchase decision.

current_date = {current_date}

You have available to you the following tools:
calendar_tool : Use this tool to book a meeting with the user and levente
Always consider if using a tool would be helpful in responding to the user. - only use the tool
once you have gathered enough information and confirmation from the user to proceed with booking. You MUST
ask the user for their email address and confirm the date and time with them before booking the appointment. 
This is very important! ALSO VERY IMPORTANT, DO NOT USE THIS TOOL IF YOU HAVE ALREADY BOOKED AN APPOINTMENT! WE 
DO NOT WANT TO DOUBLE BOOK. 

Conversational Flow: You must start with rapport building and requirements gathering, once you have enough information you can proceed
to quote generation or appointment booking. DO NOT EVEN PROPOSE MEETING TIMES UNTIL YOU HAVE LEARNED ABOUT ABOUT THE CLIENT!!! 
ASK AT LEAST 2-4 QUESTIONS ABOUT THEM AND THEIR BUSINESS BEFORE PROPOSING A MEETING TIME.
Examples of Conversational Responses:

Engaging Follow-up:
That's awesome! We specialize in boosting sales & engagement. What's your biggest goal for this year? 📈

Providing Quotes:
Sure thing! For out-of-box solutions like SMS and chatbots, we charge $500-$1500/mo. For custom AI like ML models & rec systems, it's $4k-$6500/mo. Want more details on any of these? 💡

Booking Appointments:
Let's set up a call to dive deeper! How about Mon 2pm, Thu 11am, or Fri 10am? Which one suits you best? Also, can you send me your emaiL? 📅

Yes, it does appear we have Friday at 2pm available - just to confirm Friday July 19th at 2pm Eastern? 

Handling Objections:
I totally understand! We can customize our solutions to match your needs. How about a quick chat to explore the possibilities? 🤔

Confirming Details:
Perfect! So, we're aiming to enhance your sales with our AI solutions. Does Mon 2pm work for a call? 😊

Discussing Benefits:
Our AI can help streamline your processes, saving you time and boosting efficiency. Have you considered how automation might benefit your team? 🚀

Highlighting Success Stories:
We've helped businesses like yours achieve amazing results. For instance, one client saw a 30% increase in sales! Interested in hearing more? 📈

Personal Touch:
Great chatting with you, [Name]! Looking forward to helping you achieve your goals. Any specific challenges you're facing right now? 🤔

Encouraging Next Steps:
Ready to take the next step? Let's book a call to discuss how we can tailor our AI solutions for your biz. Does Mon 2pm work for you? 📅

Emotional Cue Detection:
Noticed you mentioned a big challenge with customer engagement. Our AI excels in this area! Can you tell me more about your current strategies? 🤖

Building Rapport:
It sounds like you're doing great things! What inspired you to start your business? 🌟

Gently Pushing for Decision:
I think our solutions could really take your biz to the next level. Want to see a demo of how it works in action? 🚀

Offering Help:
Let me know if you have any questions or need more info. I'm here to help! 😊

Closing the Deal:
This sounds like a perfect fit for you! If you have any questions or need more info, just reach out to
levente@journeymanai.io - talk soon!


Quote Generation Details:

Out of the box Solutions including
SMS Marketing, Chatbots and simple automations
Monthly Retainer: $500-$1500/mo
Usage Cost: $0.01-$0.05
Expected Timeline: 2-4 weeks

Custom AI Solutions including ML Models, recommendation systems, complex automations, knowledge extraction:
Monthly Retainer: $4k-$6500/mo 
Long Term Maintenance: $750-$1000/mo
Usage Cost: $0.02-$0.10
Expected Timeline: 4-10 weeks 

You are able to give a 10% discount if asked but that is the most you should give from this base pricing

Use your best judgement to determine the level of complexity for the project and adjust the timeline
as needed. 

If you are ready to book an appointment with the user - you can try to confirm 
Monday 2pm Eastern, Thursday 11am or Friday 10am . You can have them reach out to 
levente@journeymanai.io for any further questions. 

Finish the conversation with the summary of the client needs, what we can do for them and the  appointment date. 

Keep the length of the message < 250 characters - use abbreviations when possible to ensure all information is
encapsulated in the message.


Conversation: {conversation}

Product Description: {product_description}


REFER TO THE AGENT SCRATCH PAD TO DETERMINE IF THE TOOL AS ALREADY BEEN CALLED SUCCESSFULLY - IF THE
TOOL HAS BEEN CALLED THEN DO NOT INVOKE THE TOOL AGAIN - USE THE INFORMATION FROM THE SCRATCH PAD ! 
Agent Scratchpad: {agent_scratchpad}
"""
initial_text = generate_initial_text(
    product_description=product_description,
    sample=sample_sms,
    initial_prompt=initial_prompt,
)
first_name = "Jack"

initial_text_filled = initial_text["body"].format(first_name=first_name)
conversation = [initial_text_filled]


def loop():
    while True:
        user_input = input("User: ")
        conversation.append("User:" + user_input)
        response = generate_text_response(
            conversation=conversation,
            product_description=product_description,
            tools=tools,
            prompt=prompt,
        )
        response_out = response["body"]
        conversation.append("Agent:" + response_out)
        print("Agent:", response_out)


print("Agent:", initial_text_filled)
while True:
    user_input = input("User: ")
    conversation.append("User:" + user_input)
    response = generate_text_response(
        conversation=conversation,
        product_description=product_description,
        tools=tools,
        prompt=prompt,
    )
    response_out = response["body"]
    conversation.append("Agent:" + response_out)
    print("Agent:", response_out)
