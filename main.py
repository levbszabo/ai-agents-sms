from models import SMS_Logs
import os
from fastapi import FastAPI, Request, HTTPException, Depends, Response
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
import json
from langchain.prompts import PromptTemplate
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel as BaseModelLangchain
from langchain_core.pydantic_v1 import Field as FieldLangchain
from twilio.request_validator import RequestValidator
from fixtures import SAMPLE_SMS as sample_sms
from starlette.datastructures import FormData

# run this with
# uvicorn main:app --reload

# Database imports
from models import Base, User, Agent
from models import Conversation, Message, engine, SessionLocal

# Initialize FastAPI app
app = FastAPI()

# Environment variables for API keys and tokens
api_key = os.getenv("OPENAI_API_KEY")
org_id = os.getenv("OPENAI_ORG_ID")
twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
client = Client(twilio_account_sid, twilio_auth_token)


class GenerateSMSRequest(BaseModel):
    product_description: str
    agent_id: int


class SMSRequest(BaseModel):
    phone_number: str
    initial_text: str
    product_description: str
    agent_id: int


class TextMessage(BaseModelLangchain):
    body: str = FieldLangchain(description='The body of the text message')


# Langchain AI Functions

def generate_initial_text(product_description, sample, initial_prompt):
    parser = JsonOutputParser(pydantic_object=TextMessage)
    model = ChatOpenAI(api_key=api_key, organization=org_id,
                       model='gpt-4o', temperature=0.0, max_tokens=1000)
    prompt = PromptTemplate(
        template=initial_prompt,
        input_variables=["sample", "product_description"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | model | parser
    out = chain.invoke(
        {"product_description": product_description, "sample": sample})
    return {'product_description': product_description, 'body': out['body']}


def generate_text_response(conversation, product_description, prompt):
    parser = JsonOutputParser(pydantic_object=TextMessage)
    model = ChatOpenAI(api_key=api_key, organization=org_id,
                       model='gpt-4o', temperature=0.0, max_tokens=500)
    prompt_template = PromptTemplate(
        template=prompt,
        input_variables=["conversation", "product_description"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()},
    )
    chain = prompt_template | model | parser
    out = chain.invoke({"conversation": conversation,
                       "product_description": product_description})
    return {'product_description': product_description, 'body': out['body']}


# DB Related Functions

def get_db():
    """
    Dependency to get the database session.

    :yield: The database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def write_logs(db: Session, endpoint, request, response, status):
    """
    Write logs to the database.

    :param db: The database session
    :param endpoint: The API endpoint being logged
    :param request: The request data
    :param response: The response data
    :param status: The HTTP status code
    :return: The log object
    """
    def to_serializable(val):
        if isinstance(val, dict):
            return val
        if hasattr(val, 'dict'):
            return val.dict()
        if isinstance(val, Response):
            return {
                "content": val.body.decode(),  # Decode bytes to string
                "media_type": val.media_type
            }
        if isinstance(val, FormData):
            return {key: val[key] for key in val}
        return str(val)

    log = SMS_Logs(
        endpoint=endpoint,
        request=json.dumps(to_serializable(request)),  # Serialize to JSON
        response=json.dumps(to_serializable(response)),  # Serialize to JSON
        status=status
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_or_create_user(db: Session, phone_number: str, name: str = None):
    """
    Retrieve a user by phone number, or create a new one if it doesn't exist.

    :param db: The database session
    :param phone_number: The user's phone number
    :param name: The user's name (optional)
    :return: The user object
    """
    user = db.query(User).filter_by(
        phone_number=phone_number).first()
    if not user:
        user = User(phone_number=phone_number, name=name)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_agent(db: Session, agent_id: int = None, phone_number: str = None):
    """
    Retrieve an agent by agent_id or phone number.

    :param db: The database session
    :param agent_id: The agent's ID (optional)
    :param phone_number: The agent's phone number (optional)
    :return: The agent object
    :raises ValueError: If neither agent_id nor phone_number is provided
    """
    if agent_id is not None:
        agent = db.query(Agent).filter_by(agent_id=agent_id).first()
    elif phone_number is not None:
        agent = db.query(Agent).filter_by(
            phone_number=phone_number).first()
    else:
        raise ValueError("Either agent_id or agent_phone must be provided.")
    return agent


def get_or_create_conversation(db: Session, user_id: int, agent_id: int, product_description: str = None):
    conversation = db.query(Conversation).filter_by(
        user_id=user_id, agent_id=agent_id, status='ongoing').first()
    if not conversation:
        conversation = Conversation(
            user_id=user_id, agent_id=agent_id, product_description=product_description)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    return conversation


def add_message(db: Session, conversation_id: int, sender: str, receiver: str, content: str):
    """
    Add a message to a conversation.

    :param db: The database session
    :param conversation_id: The conversation's ID
    :param sender: The sender's phone number
    :param receiver: The receiver's phone number
    :param content: The message content
    """
    message = Message(conversation_id=conversation_id,
                      sender_phone_number=sender, receiver_phone_number=receiver, content=content)
    db.add(message)
    db.commit()


# ENDPOINTS


@app.post("/generate-initial-sms")
def generate_initial_sms(request: GenerateSMSRequest, db: Session = Depends(get_db)):
    """
    Endpoint to generate the initial SMS message.

    :param request: The SMS request information
    :param db: The database session
    :return: The generated initial SMS text
    :raises HTTPException: If an error occurs during SMS generation
    """
    try:
        agent = get_agent(db, agent_id=request.agent_id)
        initial_text = generate_initial_text(
            request.product_description, sample_sms, agent.initial_prompt)['body']
        response = {'initial_text': initial_text}
        write_logs(db, 'generate-initial-sms', request, response, status=200)
        return {'initial_text': initial_text}
    except Exception as e:
        write_logs(db, 'generate-initial-sms', request,
                   {'error': str(e)}, status=500)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send-initial-sms")
def send_initial_sms(request: SMSRequest, db: Session = Depends(get_db)):
    """
    Endpoint to send the initial SMS message.

    :param request: The SMS request information
    :param db: The database session
    :return: The Twilio message SID
    :raises HTTPException: If an error occurs during SMS sending
    """
    try:
        # Generate initial text
        agent_id = request.agent_id
        agent = get_agent(db, agent_id=agent_id)
        # Send SMS using Twilio
        message = client.messages.create(
            body=request.initial_text,
            from_=twilio_phone_number,
            to=request.phone_number
        )

        # Get or create user
        user = get_or_create_user(db, request.phone_number)

        # Get or create conversation with job details
        conversation = get_or_create_conversation(
            db, user.user_id, agent_id, request.product_description)

        # Add initial agent message to the conversation
        add_message(db, conversation.conversation_id,
                    agent.phone_number, user.phone_number, request.initial_text)
        response = {"message_sid": message.sid}
        write_logs(db, 'send-initial-sms', request, response, status=200)
        return response
    except Exception as e:
        write_logs(db, 'send-initial-sms', request,
                   {'error': str(e)}, status=500)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sms")
async def sms_reply(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint to handle incoming SMS replies and generate appropriate responses.

    :param request: The incoming request
    :param db: The database session
    :return: The Twilio response XML
    :raises HTTPException: If an error occurs during SMS handling
    """

    # validator = RequestValidator(twilio_auth_token)
    # url = str(request.url)
    # signature = request.headers.get("X-Twilio-Signature", "")
    form = await request.form()
    # post_vars = {key: value for key, value in form.items()}
    agent_phone_number = form.get("To")
    phone_number = form.get('From')
    message_content = form.get('Body')
    # if not validator.validate(url, post_vars, signature):
    #     raise HTTPException(
    #         status_code=403, detail="Invalid request signature.")
    try:
        # Convert form data to dictionary for logging
        form_data = {key: form[key] for key in form.keys()}

        # Get or create user
        agent = get_agent(db, agent_id=None, phone_number=agent_phone_number)
        user = get_or_create_user(db, phone_number)

        # Get or create conversation
        conversation = get_or_create_conversation(
            db, user.user_id, agent.agent_id)
        print(conversation.messages)
        # Add user message to the conversation
        add_message(db, conversation.conversation_id, phone_number,
                    agent.phone_number, message_content)

        # Check if the conversation length is zero
        if len(conversation.messages) == 0:
            error = "No conversation history found."
            write_logs(db, 'sms', form_data, {"error": error}, 400)
            raise HTTPException(status_code=400, detail=error)

        # Retrieve the job title and description from the conversation
        product_description = conversation.product_description

        # Retrieve all previous messages with "user" or "agent" as the speaker
        conversation_history = []
        for msg in conversation.messages:
            if msg.sender_phone_number == user.phone_number:
                speaker = "user"
            elif msg.sender_phone_number == agent.phone_number:
                speaker = "agent"
            else:
                speaker = "unknown"
            conversation_history.append(
                {"speaker": speaker, "text": msg.content})

        output = generate_text_response(
            conversation_history, product_description, agent.prompt)

        # Add agent message to the conversation
        add_message(db, conversation.conversation_id,
                    agent.phone_number, user.phone_number, output['body'])

        # Create Twilio response
        resp = MessagingResponse()
        resp.message(output['body'])
        response_xml = str(resp)
        final_response = Response(
            content=response_xml, media_type="application/xml")

        # Log the final response content in JSON format
        write_logs(db, 'sms', form_data, {
                   "content": output['body'], "media_type": "application/xml"}, 200)
        return final_response
    except Exception as e:
        print(str(e))
        form_data = {key: form[key] for key in form.keys()}
        write_logs(db, 'sms', form_data, {'error': str(e)}, 500)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
