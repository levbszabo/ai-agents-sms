from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Agent  # Import your models
import os

# Define your database URL
DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/"
    f"{os.getenv('DB_NAME')}"
)

# Create an engine and a session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to add a new agent


def add_agent(phone_number, name, initial_prompt, prompt):
    session = SessionLocal()
    try:
        new_agent = Agent(
            phone_number=phone_number,
            name=name,
            initial_prompt=initial_prompt,
            prompt=prompt
        )
        session.add(new_agent)
        session.commit()
        print("New agent added successfully!")
    except Exception as e:
        session.rollback()
        print(f"Error adding agent: {e}")
    finally:
        session.close()


phone_number = os.getenv('TWILIO_PHONE_NUMBER')
name = 'SMS_Sales_AgentV2_Journeyman'
initial_prompt = """Write a short text message, in the voice of a friendly Sales Agent. The message should briefly 
summarize the important aspects of the product/service we are pitching, highlighting to the recipient why they may 
wish to implement the service. This text should come from Levente from Journeyman AI. It should make it clear that 
we can both generate a quote or book an appointment. Keep it short, direct, and use abbreviations where appropriate. 
Use the format from the sample below as a guide, and ensure you leave the first name open as indicated.

Sample: {sample}

{format_instructions}

Product Description: {product_description}"""

prompt = """
Write a short text message, in the voice of a friendly sales agent. The message should respond 
to the users text message and move the conversation forward. Use the conversation history as well as the
product description to answer any questions the user may have about the product. You are polite, direct and 
keep your messages relatively brief.

If you are looking to generate a quote you can pitch the following pricing 
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

Finish the conversation with the summary of the client needs, what we can do form them and the 
appointment date. 

Conversation: {conversation}

Product Description: {product_description}

{format_instructions}
"""
add_agent(phone_number, name, initial_prompt, prompt)
