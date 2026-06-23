import os
import asyncio
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import logging
import uuid
from datetime import datetime

from database.models import SessionLocal, Room, Message, Integration, RCA
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WarRoom_API")

app = FastAPI(title="WarRoom Production API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Integrations API ---
class IntegrationConfig(BaseModel):
    id: str
    config: dict

@app.get("/api/integrations")
async def get_integrations(db: Session = Depends(get_db)):
    ints = db.query(Integration).all()
    # Mask secrets before returning
    safe_ints = []
    for i in ints:
        safe_config = dict(i.config)
        for k in safe_config.keys():
            if "token" in k.lower() or "key" in k.lower():
                safe_config[k] = "********" if safe_config[k] else ""
        safe_ints.append({"id": i.id, "config": safe_config})
    return safe_ints

@app.post("/api/integrations")
async def save_integration(data: IntegrationConfig, db: Session = Depends(get_db)):
    # Merge existing config to avoid overwriting tokens with '********'
    existing = db.query(Integration).filter(Integration.id == data.id).first()
    new_config = data.config
    
    if existing:
        for k, v in new_config.items():
            if v == "********":
                new_config[k] = existing.config.get(k, "")
        existing.config = new_config
        existing.updated_at = datetime.utcnow()
    else:
        new_int = Integration(id=data.id, config=new_config)
        db.add(new_int)
        
    db.commit()
    return {"status": "success"}

# --- Config API (Frontend Integration Settings) ---
from config import settings, save_settings

@app.get("/api/config")
async def get_config():
    return {
        "splunk_mcp_url": settings.splunk_mcp_url,
        "has_splunk_token": bool(settings.splunk_mcp_token),
        "has_splunk_hosted_key": bool(settings.splunk_hosted_key),
        "has_vt_key": bool(settings.vt_api_key),
        "ollama_model": settings.ollama_model,
        "has_llm_key": bool(settings.llm_api_key),
        "llm_api_base": settings.llm_api_base,
        "jira_mcp_url": settings.jira_mcp_url,
        "has_jira_token": bool(settings.jira_mcp_token),
        "has_slack_bot_token": bool(settings.slack_bot_token),
        "has_slack_app_token": bool(settings.slack_app_token)
    }

@app.post("/api/config")
async def update_config(data: dict):
    save_settings(data)
    return {"status": "success"}

# --- Rooms API ---
class RoomCreate(BaseModel):
    title: str

@app.get("/api/rooms")
async def list_rooms(db: Session = Depends(get_db)):
    rooms = db.query(Room).order_by(Room.created_at.desc()).all()
    return [{
        "id": r.id, 
        "title": r.title, 
        "source": r.source,
        "severity": r.severity,
        "participants": r.participants,
        "evidence": r.evidence,
        "timeline": r.timeline,
        "created_at": r.created_at, 
        "status": r.status
    } for r in rooms]

@app.get("/api/rooms/{room_id}")
async def get_room(room_id: str, db: Session = Depends(get_db)):
    r = db.query(Room).filter(Room.id == room_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Room not found")
    return {
        "id": r.id, 
        "title": r.title, 
        "source": r.source,
        "severity": r.severity,
        "participants": r.participants,
        "evidence": r.evidence,
        "timeline": r.timeline,
        "created_at": r.created_at, 
        "status": r.status
    }

@app.post("/api/rooms")
async def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    new_room = Room(
        id=str(uuid.uuid4()), 
        title=room.title,
        source="Web App",
        severity="P2 - High",
        participants=["WarRoom AI", "SOC Analyst"],
        evidence=[],
        timeline=[]
    )
    db.add(new_room)
    db.commit()
    return {"id": new_room.id, "title": new_room.title}

@app.get("/api/rooms/{room_id}/messages")
async def get_messages(room_id: str, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.room_id == room_id).order_by(Message.created_at.asc()).all()
    return [{"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at} for m in messages]

class ChatMessage(BaseModel):
    room_id: str
    message: str
    sender_name: Optional[str] = "User"
    room_title: Optional[str] = None
    room_description: Optional[str] = None
    incident_commander: Optional[str] = None
    collaborators: Optional[list] = None

@app.post("/api/chat/silent")
async def silent_chat_endpoint(chat: ChatMessage, db: Session = Depends(get_db)):
    """Ingests a message into the room's history without triggering an AI response.
    Useful for passively listening to Slack channels."""
    if not chat.message or not chat.message.strip():
        return {"status": "ignored", "reason": "empty message"}

    # Ensure room exists
    room = db.query(Room).filter(Room.id == chat.room_id).first()
    if not room:
        title = chat.room_title
        if not title:
            display_name = chat.room_id.replace('slack_channel_', '#').replace('slack_thread_', 'Thread ')
            title = f"Slack Investigation ({display_name})"
        room = Room(
            id=chat.room_id, 
            title=title, 
            source="Slack",
            description=chat.room_description,
            incident_commander=chat.incident_commander,
            collaborators=chat.collaborators or []
        )
        db.add(room)
        db.commit()
    else:
        # Update metadata if provided
        updated = False
        if chat.room_description and room.description != chat.room_description:
            room.description = chat.room_description
            updated = True
        if chat.incident_commander and room.incident_commander != chat.incident_commander:
            room.incident_commander = chat.incident_commander
            updated = True
        if chat.collaborators is not None and room.collaborators != chat.collaborators:
            room.collaborators = chat.collaborators
            updated = True
        if updated:
            db.commit()
    
    # Save the user's message silently
    msg_content = f"{chat.sender_name}: {chat.message}" if chat.sender_name != "User" else chat.message
    msg = Message(room_id=chat.room_id, role="user", content=msg_content)
    db.add(msg)
    db.commit()
    return {"status": "success", "message_id": msg.id}

@app.post("/api/chat")
async def chat_endpoint(chat: ChatMessage, db: Session = Depends(get_db)):
    """Production Chat endpoint. Handles history and tool execution."""
    if not chat.message or not chat.message.strip():
        return {"response": "I cannot process an empty message. Please provide details."}

    # Ensure room exists
    room = db.query(Room).filter(Room.id == chat.room_id).first()
    if not room:
        title = chat.room_title or "Test Web Chat"
        if chat.room_id.startswith("slack_") and not chat.room_title:
            display_name = chat.room_id.replace('slack_channel_', '#').replace('slack_thread_', 'Thread ').replace('slack_dm_', '@')
            title = f"Slack Investigation ({display_name})"
        new_room = Room(
            id=chat.room_id, 
            title=title, 
            source="Slack" if chat.room_id.startswith("slack_") else "Web App",
            description=chat.room_description,
            incident_commander=chat.incident_commander,
            collaborators=chat.collaborators or []
        )
        db.add(new_room)
        db.commit()
        room = new_room
    else:
        # Update metadata if provided
        updated = False
        if chat.room_description and room.description != chat.room_description:
            room.description = chat.room_description
            updated = True
        if chat.incident_commander and room.incident_commander != chat.incident_commander:
            room.incident_commander = chat.incident_commander
            updated = True
        if chat.collaborators is not None and room.collaborators != chat.collaborators:
            room.collaborators = chat.collaborators
            updated = True
        if updated:
            db.commit()  # Save user message
    user_msg = Message(room_id=chat.room_id, role="user", content=chat.message)
    db.add(user_msg)
    db.commit()

    # Get history
    history = db.query(Message).filter(Message.room_id == chat.room_id).order_by(Message.created_at.asc()).all()
    history_dicts = [{"role": m.role, "content": m.content} for m in history]

    from agent.orchestrator import IncidentCommander
    
    try:
        # Process through agent
        agent = IncidentCommander(room_id=chat.room_id)
        reply = await agent.run(user_prompt=chat.message)
        await agent.close()
    except Exception as e:
        logger.error(f"Agent error: {e}")
        reply = f"Error during investigation: {str(e)}"
    
    # Save assistant message
    ai_msg = Message(room_id=chat.room_id, role="assistant", content=reply)
    db.add(ai_msg)
    db.commit()
    
    return {"response": reply}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
