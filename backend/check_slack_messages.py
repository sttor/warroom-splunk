import urllib.request
import json

try:
    req = urllib.request.Request("http://127.0.0.1:8000/api/rooms")
    with urllib.request.urlopen(req) as response:
        rooms = json.loads(response.read().decode())
        
    slack_rooms = [r for r in rooms if str(r.get("id")).startswith("slack_")]
    
    if not slack_rooms:
        print("No Slack rooms found in the backend yet.")
    else:
        for r in slack_rooms:
            print(f"\nFound Slack Room: {r.get('id')}")
            # Fetch messages for this room
            msg_req = urllib.request.Request(f"http://127.0.0.1:8000/api/rooms/{r.get('id')}/messages")
            with urllib.request.urlopen(msg_req) as msg_res:
                msgs = json.loads(msg_res.read().decode())
                for m in msgs[-5:]:
                    print(f"  [{m.get('role')}] {m.get('content')}")
except Exception as e:
    print(f"Error checking backend API: {e}")
