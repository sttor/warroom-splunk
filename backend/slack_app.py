import logging
import asyncio
import re
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from config import settings
from database.models import SessionLocal, Message, Room
from agent.orchestrator import WarRoomAgent

logger = logging.getLogger("WarRoom_SlackApp")

app_token = settings.slack_bot_token if settings.slack_bot_token else "xoxb-dummy"
app = AsyncApp(token=app_token)

def get_or_create_room(channel_id: str) -> str:
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.id == channel_id).first()
        if not room:
            room = Room(id=channel_id, title=f"Slack Room {channel_id}", source="Slack")
            db.add(room)
            db.commit()
        return channel_id
    finally:
        db.close()

def save_raw_message(channel_id: str, role: str, content: str):
    db = SessionLocal()
    try:
        msg = Message(room_id=channel_id, role=role, content=content)
        db.add(msg)
        db.commit()
    finally:
        db.close()

@app.event("app_mention")
async def handle_app_mentions(event, say, logger):
    """
    The Responder: Handles when someone tags @WarRoom in a channel.
    """
    user_id = event.get("user")
    text = event.get("text")
    channel = event.get("channel")
    ts = event.get("ts")
    
    # Extract the actual command by removing the mention
    command = re.sub(r'<@U[A-Z0-9]+>', '', text).strip()
    
    get_or_create_room(channel)
    save_raw_message(channel, "user", f"<@{user_id}>: {command}")

    # Acknowledge receipt
    await say(text=f"Copy that <@{user_id}>, investigating now... 🔍", thread_ts=ts)
    
    # Initialize Agent and run
    try:
        agent = WarRoomAgent(room_id=channel)
        result_text = await agent.run(user_prompt=command)
        await agent.close()
    except Exception as e:
        logger.error(f"Agent Error: {e}")
        result_text = f"Encountered an error while running the investigation: {e}"

    # Reply with Block Kit
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": result_text
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Isolate Host",
                        "emoji": True
                    },
                    "style": "danger",
                    "value": "isolate_host"
                }
            ]
        }
    ]
    
    await say(blocks=blocks, text="Investigation Results", thread_ts=ts)


@app.action("isolate_host")
async def handle_isolate_action(ack, body, logger, say):
    await ack()
    user_id = body["user"]["id"]
    await say(f"⚠️ *<@{user_id}> has initiated a containment playbook to isolate the host.*")

@app.event("message")
async def handle_message_events(event, logger, say):
    """
    The Scribe: Listens to all messages in the channel.
    Builds timeline in Postgres and automatically reads Jira tickets.
    """
    channel = event.get("channel")
    text = event.get("text")
    user_id = event.get("user")
    ts = event.get("ts")
    
    if not text or not user_id:
        return
        
    get_or_create_room(channel)
    save_raw_message(channel, "user", f"<@{user_id}>: {text}")
    
    # Detect Jira Tickets (e.g., SEC-123, PROJ-456)
    jira_matches = set(re.findall(r'[A-Z]{2,}-\d+', text))
    if jira_matches and settings.jira_mcp_url:
        for ticket in jira_matches:
            try:
                # Silently invoke agent to just read the ticket
                # This could be run in the background without replying,
                # but for hackathon demo, we reply in thread.
                agent = WarRoomAgent(room_id=channel)
                summary = await agent.run(f"Silently fetch Jira ticket {ticket} using tools and summarize its status, assignee, and description in 2 sentences. Do not mention Splunk.")
                await agent.close()
                
                await say(
                    text=f"🎫 *Jira Context for {ticket}:*\n{summary}",
                    thread_ts=ts
                )
            except Exception as e:
                logger.error(f"Jira fetch error: {e}")

async def start_slack_app():
    """Starts the socket mode handler."""
    try:
        handler = AsyncSocketModeHandler(app, settings.slack_app_token)
        await handler.start_async()
    except Exception as e:
        logger.error(f"Failed to start Slack App: {e}")
