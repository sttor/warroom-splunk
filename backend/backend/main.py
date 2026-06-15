print("TOP OF MAIN")
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import logging
import asyncio
import os
import json

from config import settings
from splunk_mcp.client import SplunkMCPClient
from agent.orchestrator import WarRoomAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WarRoom_API")

app = FastAPI(title="WarRoom API", description="AI Incident Commander")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
print("Initializing settings...")
splunk_client = SplunkMCPClient(settings)
print("Splunk client initialized.")
# orchestrator = WarRoomAgent(splunk_client, settings.llm_provider, settings.openai_api_key, settings.llm_model)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")

chat_manager = ConnectionManager()
graph_manager = ConnectionManager()

@app.get("/api/rooms")
async def get_rooms():
    return [
        {
            "id": "WAR-101",
            "title": "Suspected Credential Theft via VPN",
            "severity": "P0",
            "status": "Active",
            "assignee": "AI Agent",
            "source": "Splunk ES",
            "created_at": "2026-06-13T10:00:00Z"
        },
        {
            "id": "WAR-102",
            "title": "Multiple Failed Logins on DB Server",
            "severity": "P1",
            "status": "Investigating",
            "assignee": "Alex",
            "source": "Okta",
            "created_at": "2026-06-13T11:30:00Z"
        },
        {
            "id": "WAR-103",
            "title": "Suspicious Outbound Traffic to Unknown IP",
            "severity": "P2",
            "status": "Resolved",
            "assignee": "Sarah",
            "source": "Palo Alto",
            "created_at": "2026-06-12T09:15:00Z"
        }
    ]

@app.get("/api/rooms/{room_id}")
async def get_room(room_id: str):
    # Dummy mock data for a single room
    return {
        "id": room_id,
        "title": f"Investigation for {room_id}",
        "severity": "P1",
        "status": "Active",
        "assignee": "AI Agent",
        "source": "Splunk ES",
        "created_at": "2026-06-13T10:00:00Z"
    }

@app.on_event("startup")
async def startup_event():
    logger.info("Starting WarRoom API...")
    # Initialize Splunk client
    try:
        await splunk_client.connect()
        logger.info("Connected to Splunk (or running in Demo Mode).")
    except Exception as e:
        logger.error(f"Failed to connect to Splunk: {e}")

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    await chat_manager.connect(websocket)
    try:
        # Welcome message
        welcome = {"sender": "System", "message": "WarRoom WarRoom Initialized. Connected to Splunk MCP Server. How can I assist with your investigation today?", "type": "chat"}
        await websocket.send_text(json.dumps(welcome))
        
        # Callback to stream updates from agent to client
        async def send_update(sender, message):
            if isinstance(message, dict) and message.get("type") in ["node", "edge"]:
                # This is a graph event triggered by chat, route to graph connections
                await graph_manager.broadcast(json.dumps(message))
            else:
                # Normal chat stream
                payload = {"sender": sender, "message": message, "type": "chat"}
                await websocket.send_text(json.dumps(payload))

        while True:
            data = await websocket.receive_text()
            # User sent a message
            user_msg = {"sender": "Analyst", "message": data, "type": "chat"}
            await websocket.send_text(json.dumps(user_msg)) # Echo back to UI
            
            # Process via Orchestrator
            await orchestrator.chat_agent.process_message(session_id, data, send_update)
            
    except WebSocketDisconnect:
        chat_manager.disconnect(websocket)
        logger.info(f"Chat Session {session_id} disconnected")

@app.websocket("/ws/graph/{session_id}")
async def websocket_graph_endpoint(websocket: WebSocket, session_id: str):
    await graph_manager.connect(websocket)
    try:
        while True:
            # Just keep connection alive, the backend pushes data to this socket
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        graph_manager.disconnect(websocket)
        logger.info(f"Graph Session {session_id} disconnected")


# Mount the frontend directory directly at the root
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "out")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    logger.warning(f"Frontend directory not found at {frontend_dir}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
