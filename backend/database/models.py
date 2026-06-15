from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Read from env or default to SQLite for fallback if Postgres isn't running
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./warroom.db")

# Only use check_same_thread for SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Room(Base):
    """An investigation chat session"""
    __tablename__ = "rooms"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, default="New Investigation")
    source = Column(String, default="Web App") # e.g. "Web App", "Slack"
    severity = Column(String, default="P3 - Medium") # e.g. "P1 - Critical"
    participants = Column(JSON, default=list) # List of participant names
    evidence = Column(JSON, default=list) # List of pinned indicators/evidence
    timeline = Column(JSON, default=list) # Chronological events for RCA
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active") # active, closed
    
    # Relationships
    messages = relationship("Message", back_populates="room")
    rca = relationship("RCA", back_populates="room", uselist=False)

class Message(Base):
    """A message inside a room"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, ForeignKey("rooms.id"))
    role = Column(String) # user, assistant, system, tool
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    room = relationship("Room", back_populates="messages")

class Integration(Base):
    """Stores client settings for external tools"""
    __tablename__ = "integrations"

    id = Column(String, primary_key=True) # e.g. "splunk", "virustotal"
    config = Column(JSON) # e.g. {"url": "...", "token": "..."}
    updated_at = Column(DateTime, default=datetime.utcnow)

class RCA(Base):
    """Root Cause Analysis for an investigation"""
    __tablename__ = "rcas"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, ForeignKey("rooms.id"))
    summary = Column(Text)
    root_cause = Column(Text)
    mitigation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    room = relationship("Room", back_populates="rca")

# Create tables
Base.metadata.create_all(bind=engine)
