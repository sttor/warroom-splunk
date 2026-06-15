import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WarRoom_Orchestrator")

class WarRoomAgent:
    """
    Handles natural language chat interaction with the SOC analyst.
    Translates intents to SPL via Splunk AI Assistant and executes via MCP.
    """
    def __init__(self, splunk_client, llm_provider: str, api_key: str, model: str):
        self.splunk = splunk_client
        self.provider = llm_provider
        self.api_key = api_key
        self.model = model
        # Keep track of conversation history per session
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        
    async def process_message(self, session_id: str, message: str, send_update: Callable) -> str:
        """Process an incoming chat message."""
        if session_id not in self.sessions:
            self.sessions[session_id] = [
                {"role": "system", "content": "You are WarRoom, an AI Security Operations Center (SOC) Incident Commander. You assist analysts in investigating security incidents. You can query Splunk to find information."}
            ]
            
        self.sessions[session_id].append({"role": "user", "content": message})
        
        # In a real implementation, this would call the LLM API with function calling tools.
        # The tools would include: `generate_spl(natural_language)`, `run_splunk_query(spl)`.
        
        # --- DEMO MODE MOCK LOGIC ---
        await send_update("Agent", f"Analyzing request: '{message}'...")
        await asyncio.sleep(1)
        
        if "investigate" in message.lower() and "10.0.0.5" in message:
            await send_update("System", "Calling Splunk AI Assistant (saia_generate_spl)...")
            await asyncio.sleep(1)
            await send_update("System", "Generated SPL: `search index=botsv1 src_ip=\"10.0.0.5\" | stats count by dest_ip`")
            await asyncio.sleep(1)
            await send_update("System", "Executing query via Splunk MCP Server...")
            await asyncio.sleep(2)
            
            response = "I have investigated IP `10.0.0.5`. I found 15 connections to internal servers. I have initiated a BlastRadius scan for this IP. You will see the results on the graph shortly."
            
            # Trigger BlastRadius in background (mock trigger)
            # In real life, we'd emit an event or call the BlastAgent directly
            asyncio.create_task(self._trigger_mock_blast_radius(send_update))
            
        elif "download" in message.lower() or "file" in message.lower():
            response = "I checked the proxy logs. The user downloaded a 500MB ZIP file named 'q3_financials.zip' from an external file-sharing site."
        else:
            response = "I can help you investigate that. Would you like me to pull the firewall logs or the authentication logs?"
            
        self.sessions[session_id].append({"role": "assistant", "content": response})
        return response

    async def _trigger_mock_blast_radius(self, send_update: Callable):
        """Mock the discovery of nodes for the graph."""
        await asyncio.sleep(2)
        await send_update("GraphEvent", {"type": "node", "id": "10.0.0.5", "label": "10.0.0.5", "group": "ip", "color": "#ef4444"})
        await asyncio.sleep(2)
        await send_update("GraphEvent", {"type": "node", "id": "jsmith", "label": "jsmith", "group": "user", "color": "#8b5cf6"})
        await send_update("GraphEvent", {"type": "edge", "source": "10.0.0.5", "target": "jsmith", "label": "logged in as"})
        await asyncio.sleep(2)
        await send_update("GraphEvent", {"type": "node", "id": "server-db-01", "label": "server-db-01", "group": "host", "color": "#eab308"})
        await send_update("GraphEvent", {"type": "edge", "source": "jsmith", "target": "server-db-01", "label": "accessed"})


class BlastRadiusAgent:
    """
    Runs autonomously in the background. Takes an IOC, recursively queries Splunk
    to find related entities, and emits graph nodes/edges.
    """
    def __init__(self, splunk_client):
        self.splunk = splunk_client
        self.visited = set()
        
    async def scan(self, initial_ioc: str, ioc_type: str, max_depth: int = 2, emit_callback: Callable = None):
        """
        Recursively scan for related IOCs.
        emit_callback is a function that sends the node/edge data to the WebSocket.
        """
        logger.info(f"Starting BlastRadius scan for {ioc_type}: {initial_ioc}")
        await self._scan_recursive(initial_ioc, ioc_type, 0, max_depth, emit_callback)
        
    async def _scan_recursive(self, ioc: str, ioc_type: str, current_depth: int, max_depth: int, emit_callback: Callable):
        if current_depth > max_depth or ioc in self.visited:
            return
            
        self.visited.add(ioc)
        
        # Emit the current node
        if emit_callback:
            await emit_callback({
                "type": "node",
                "id": ioc,
                "label": ioc,
                "group": ioc_type
            })
            
        # In a real implementation, we would construct specific SPL queries based on ioc_type
        # e.g., if IP -> find users. If user -> find IPs.
        # Run queries via self.splunk.run_query(spl)
        
        # ... logic to parse results and find new IOCs ...
        # For each new_ioc found:
        # await emit_callback({"type": "edge", "source": ioc, "target": new_ioc, "label": "connected to"})
        # await self._scan_recursive(new_ioc, new_type, current_depth + 1, max_depth, emit_callback)

class Orchestrator:
    """Main orchestrator that manages both agents."""
    def __init__(self, splunk_client, config):
        self.chat_agent = WarRoomAgent(
            splunk_client, 
            config.get('LLM_PROVIDER', 'demo'), 
            config.get('LLM_API_KEY', ''), 
            config.get('LLM_MODEL', '')
        )
        self.blast_agent = BlastRadiusAgent(splunk_client)
