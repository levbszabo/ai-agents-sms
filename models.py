from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

Base = declarative_base()

username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
hostname = os.getenv('DB_HOST')
database = os.getenv('DB_NAME')


class Agent(Base):
    __tablename__ = 'Agent'
    agent_id = Column(Integer, primary_key=True)
    phone_number = Column(String(15), unique=True, nullable=False)
    name = Column(String(100))
    initial_prompt = Column(Text, nullable=True)
    prompt = Column(Text, nullable=False)


class User(Base):
    __tablename__ = 'User'
    user_id = Column(Integer, primary_key=True)
    phone_number = Column(String(15), unique=True, nullable=False)
    name = Column(String(100))
    conversations = relationship(
        'Conversation', back_populates='user')


class Conversation(Base):
    __tablename__ = 'Conversation'
    conversation_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('User.user_id'))
    agent_id = Column(Integer, ForeignKey('Agent.agent_id'))
    start_time = Column(TIMESTAMP, default=func.now())
    end_time = Column(TIMESTAMP)
    status = Column(String(20), default='ongoing')
    product_description = Column(Text)
    user = relationship('User', back_populates='conversations')
    messages = relationship('Message',
                            back_populates='conversation')
    agent = relationship('Agent')


class Message(Base):
    __tablename__ = 'Message'
    message_id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey(
        'Conversation.conversation_id'))
    sender_phone_number = Column(String(20))
    receiver_phone_number = Column(String(20))
    content = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP, default=func.now())
    conversation = relationship(
        'Conversation', back_populates='messages')


class SMS_Logs(Base):
    __tablename__ = 'SMS_Logs'
    log_id = Column(Integer, primary_key=True)
    request = Column(Text, nullable=True)
    endpoint = Column(String(20), nullable=False)
    response = Column(Text, nullable=True)
    status = Column(String(20), nullable=False)
    timestamp = Column(TIMESTAMP, default=func.now())


# Create an engine and a session
db_url = f"mysql+pymysql://{username}:{password}@{hostname}/{database}"
engine = create_engine(db_url)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
