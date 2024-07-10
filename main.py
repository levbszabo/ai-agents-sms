from models import SMS_Logs
import os
from fastapi import FastAPI, Request, HTTPException, Depends, Response
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
import json
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler
from langchain.prompts import PromptTemplate
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel as BaseModelLangchain
from langchain_core.pydantic_v1 import Field as FieldLangchain
from twilio.request_validator import RequestValidator
from fixtures import SAMPLE_SMS as sample_sms
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from starlette.datastructures import FormData
from tools import CalendarBookingTool
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from fetch_secrets import get_secret
from auth import get_api_key  # Import the auth dependency
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

secrets = get_secret()

# Set the secrets as environment variables
for key, value in secrets.items():
    os.environ[key] = value
# run this with
# uvicorn main:app --reload

# Database imports
from models import Base, User, Agent
from models import Conversation, Message, engine, SessionLocal

# Initialize FastAPI app
app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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
    body: str = FieldLangchain(description="The body of the text message")


def generate_initial_text(product_description, sample, initial_prompt):
    model = ChatOpenAI(
        api_key=api_key,
        organization=org_id,
        model="gpt-4o",
        temperature=0.0,
        max_tokens=1000,
    )
    prompt = PromptTemplate(
        template=initial_prompt,
        input_variables=["sample", "product_description"],
    )
    chain = prompt | model
    out = chain.invoke({"product_description": product_description, "sample": sample})
    return {"product_description": product_description, "body": out.content}


def generate_text_response(conversation, product_description, tools, prompt):
    EST = ZoneInfo("America/New_York")
    current_date = datetime.now(EST).strftime("%Y-%m-%d %I:%M %p")
    model = ChatOpenAI(
        api_key=api_key,
        organization=org_id,
        model="gpt-4o",
        temperature=0.0,
        max_tokens=1500,
    )
    prompt_template = PromptTemplate(
        template=prompt,
        input_variables=[
            "conversation",
            "product_description",
            "current_date",
            "agent_scratchpad",
        ],
    )
    agent = create_tool_calling_agent(model, tools, prompt_template)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    out = agent_executor.invoke(
        {
            "conversation": conversation,
            "product_description": product_description,
            "current_date": current_date,
        }
    )
    return {"product_description": product_description, "body": out["output"]}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def write_logs(db: Session, endpoint, request, response, status):
    def to_serializable(val):
        if isinstance(val, dict):
            return val
        if hasattr(val, "dict"):
            return val.dict()
        if isinstance(val, Response):
            return {
                "content": val.body.decode(),
                "media_type": val.media_type,
            }
        if isinstance(val, FormData):
            return {key: val[key] for key in val}
        return str(val)

    log = SMS_Logs(
        endpoint=endpoint,
        request=json.dumps(to_serializable(request)),
        response=json.dumps(to_serializable(response)),
        status=status,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_or_create_user(db: Session, phone_number: str, name: str = None):
    user = db.query(User).filter_by(phone_number=phone_number).first()
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
    if agent_id is None and phone_number is None:
        raise ValueError("Either agent_id or phone_number must be provided")

    if agent_id is not None:
        agent = db.query(Agent).filter_by(agent_id=agent_id).first()
        return agent

    else:
        agent = db.query(Agent).filter_by(phone_number=phone_number).first()
        return agent


def get_or_create_conversation(
    db: Session, user_id: int, agent_id: int, product_description: str = None
):
    conversation = (
        db.query(Conversation)
        .filter_by(user_id=user_id, agent_id=agent_id, status="ongoing")
        .first()
    )
    if not conversation:
        conversation = Conversation(
            user_id=user_id, agent_id=agent_id, product_description=product_description
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    return conversation


def add_message(
    db: Session, conversation_id: int, sender: str, receiver: str, content: str
):
    message = Message(
        conversation_id=conversation_id,
        sender_phone_number=sender,
        receiver_phone_number=receiver,
        content=content,
    )
    db.add(message)
    db.commit()


@app.post("/sms/generate-initial-sms")
@limiter.limit("20/minute;1000/day")
def generate_initial_sms(
    request: Request,
    body: GenerateSMSRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    try:
        agent = get_agent(db, agent_id=body.agent_id)
        initial_text = generate_initial_text(
            body.product_description, sample_sms, agent.initial_prompt
        )["body"]
        response = {"initial_text": initial_text}
        write_logs(db, "generate-initial-sms", body, response, status=200)
        return {"initial_text": initial_text}
    except Exception as e:
        write_logs(db, "generate-initial-sms", body, {"error": str(e)}, status=500)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sms/send-initial-sms")
@limiter.limit("20/minute;1000/day")
def send_initial_sms(
    request: Request,
    body: SMSRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    form_data = await request.json()
    logger.info("Received form data: %s", form_data)
    print(form_data)
    try:
        agent_id = body.agent_id
        agent = get_agent(db, agent_id=agent_id)
        message = client.messages.create(
            body=body.initial_text,
            from_=twilio_phone_number,
            to=body.phone_number,
        )

        user = get_or_create_user(db, body.phone_number)
        conversation = get_or_create_conversation(
            db, user.user_id, agent_id, body.product_description
        )
        add_message(
            db,
            conversation.conversation_id,
            agent.phone_number,
            user.phone_number,
            body.initial_text,
        )
        response = {"message_sid": message.sid}
        write_logs(db, "send-initial-sms", body, response, status=200)
        return response
    except Exception as e:
        write_logs(db, "send-initial-sms", body, {"error": str(e)}, status=500)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sms/sms")
@limiter.limit("20/minute;1000/day")
async def sms_reply(
    request: Request, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)
):
    form = await request.form()
    post_vars = {key: value for key, value in form.items()}
    print(post_vars)
    agent_phone_number = form.get("To")
    phone_number = form.get("From")
    message_content = form.get("Body")
    if post_vars.get("FromCountry") != "US":
        error = "Only US numbers are supported."
        write_logs(db, "sms", form, {"error": error}, 400)
        raise HTTPException(status_code=400, detail=error)
    try:
        form_data = {key: form[key] for key in form.keys()}
        agent = get_agent(db, agent_id=None, phone_number=agent_phone_number)
        user = get_or_create_user(db, phone_number)
        conversation = get_or_create_conversation(db, user.user_id, agent.agent_id)
        print(conversation.messages)
        add_message(
            db,
            conversation.conversation_id,
            phone_number,
            agent.phone_number,
            message_content,
        )

        if len(conversation.messages) == 0:
            error = "No conversation history found."
            write_logs(db, "sms", form_data, {"error": error}, 400)
            raise HTTPException(status_code=400, detail=error)

        product_description = conversation.product_description
        conversation_history = []
        for msg in conversation.messages:
            if msg.sender_phone_number == user.phone_number:
                speaker = "user"
            elif msg.sender_phone_number == agent.phone_number:
                speaker = "agent"
            else:
                speaker = "unknown"
            conversation_history.append({"speaker": speaker, "text": msg.content})
        calendar_tool = CalendarBookingTool()
        tools = [calendar_tool]
        output = generate_text_response(
            conversation_history, product_description, tools, agent.prompt
        )

        add_message(
            db,
            conversation.conversation_id,
            agent.phone_number,
            user.phone_number,
            output["body"],
        )

        resp = MessagingResponse()
        resp.message(output["body"])
        response_xml = str(resp)
        final_response = Response(content=response_xml, media_type="application/xml")

        write_logs(
            db,
            "sms",
            form_data,
            {"content": output["body"], "media_type": "application/xml"},
            200,
        )
        return final_response
    except Exception as e:
        print(str(e))
        form_data = {key: form[key] for key in form.keys()}
        write_logs(db, "sms", form_data, {"error": str(e)}, 500)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
