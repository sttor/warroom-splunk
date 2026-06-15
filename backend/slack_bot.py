import os
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

load_dotenv()

WARROOM_API_URL = "http://127.0.0.1:8000/api/chat"

def handle_app_mention_events(body, say):
    """Triggered when someone @mentions the bot in a channel."""
    event = body.get("event", {})
    text = event.get("text", "")
    channel_id = event.get("channel", "")
    thread_ts = event.get("thread_ts", event.get("ts"))
    
    clean_text = text.split(">", 1)[-1].strip() if ">" in text else text
    print(f"\n[RECEIVE - Mention] From Channel {channel_id}: {clean_text}")
    
    try:
        payload = {"message": clean_text, "room_id": f"slack_thread_{thread_ts}"}
        response = requests.post(WARROOM_API_URL, json=payload, timeout=120)
        
        if response.status_code == 200:
            agent_reply = response.json().get("response", "Error: Empty response")
            print(f"[SEND - Mention] Answering with {len(agent_reply)} chars...")
            say(agent_reply, thread_ts=thread_ts)
        else:
            say(f"Backend Error: {response.status_code} - {response.text}", thread_ts=thread_ts)
            
    except Exception as e:
        say(f"Connection Error: {str(e)}", thread_ts=thread_ts)

def handle_all_messages(message, say):
    """Triggered for ALL messages (DMs and Channel messages) the bot can see."""
    text = message.get("text", "")
    channel_id = message.get("channel", "")
    channel_type = message.get("channel_type")
    user = message.get("user", "UnknownUser")
    thread_ts = message.get("thread_ts")
    
    # Ignore bot's own messages
    if message.get("bot_id"):
        return

    if channel_type == "im":
        # Direct Message: Bot should actively reply
        print(f"\n[RECEIVE - DM] From User {user}: {text}")
        payload = {"message": text, "room_id": f"slack_dm_{channel_id}"}
        try:
            response = requests.post(WARROOM_API_URL, json=payload, timeout=120)
            if response.status_code == 200:
                agent_reply = response.json().get("response", "Error: Empty response")
                print(f"[SEND - DM] Answering with {len(agent_reply)} chars...")
                say(agent_reply)
            else:
                say(f"Backend Error: {response.status_code}")
        except Exception as e:
            say(f"Connection Error: {str(e)}")
    else:
        # Public/Private Channel Message: Bot should silently ingest for context/RCA
        room_id = f"slack_thread_{thread_ts}" if thread_ts else f"slack_channel_{channel_id}"
        
        print(f"\n[RECEIVE - Silent Channel] From User {user} in {channel_id}: {text}")
        payload = {
            "message": text, 
            "room_id": room_id,
            "sender_name": f"<@{user}>"
        }
        try:
            requests.post(WARROOM_API_URL + "/silent", json=payload, timeout=5)
            print(f"[SEND - Silent Channel] Successfully ingested into DB")
        except Exception as e:
            print(f"[ERROR - Silent Channel] Ingestion failed: {e}")

if __name__ == "__main__":
    import time
    
    print("⏳ Waiting for Slack tokens to be configured in Integrations UI...")
    while True:
        # Reload env to pick up UI changes
        load_dotenv(override=True)
        bot_token = os.environ.get("SLACK_BOT_TOKEN", "")
        app_token = os.environ.get("SLACK_APP_TOKEN", "")
        
        if bot_token and app_token and bot_token != "********" and app_token != "********":
            # Re-initialize the app with the correct token
            app = App(token=bot_token)
            
            # Re-bind the event handlers to the new app instance
            @app.event("app_mention")
            def _handle_app_mention_events(body, say):
                handle_app_mention_events(body, say)
                
            @app.event("message")
            def _handle_all_messages(body, say):
                event = body.get("event", {})
                handle_all_messages(event, say)

            print("⚡️ Tokens found! Starting Slack Socket Mode Bot...")
            try:
                handler = SocketModeHandler(app, app_token)
                handler.start()
                break # If it exits cleanly, we can break
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                print("Make sure your tokens are correct (xoxb-... and xapp-...)")
                print("Waiting 10 seconds before retrying...")
                time.sleep(10)
                continue
            
        time.sleep(3)
