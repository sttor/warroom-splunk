import asyncio
import json
import logging
import os
from typing import List, Dict, Any, Optional

from litellm import completion
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from database.models import SessionLocal, Message, Room
from config import settings

logger = logging.getLogger("WarRoom_Agent")

class MCPConnection:
    def __init__(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        self.name = name
        self.command = command
        self.args = args
        self.env = env
        self.session: Optional[ClientSession] = None
        self._stdio_ctx = None
        self._read = None
        self._write = None

    async def connect(self):
        # Merge current OS environment with custom env so npx/node can run
        import os
        merged_env = os.environ.copy()
        if self.env:
            merged_env.update(self.env)
        server_params = StdioServerParameters(command=self.command, args=self.args, env=merged_env)
        self._stdio_ctx = stdio_client(server_params)
        self._read, self._write = await self._stdio_ctx.__aenter__()
        self.session = ClientSession(self._read, self._write)
        await self.session.__aenter__()
        await self.session.initialize()
        logger.info(f"[{self.name}] MCP connected successfully.")

    async def disconnect(self):
        if self.session:
            await self.session.__aexit__(None, None, None)
        if self._stdio_ctx:
            await self._stdio_ctx.__aexit__(None, None, None)

    async def list_tools(self) -> List[dict]:
        tools_response = await self.session.list_tools()
        formatted_tools = []
        for t in tools_response.tools:
            # Format to OpenAI schema
            tool_schema = {
                "type": "function",
                "function": {
                    "name": f"{self.name}__{t.name}",
                    "description": t.description or f"Tool {t.name} from {self.name}",
                    "parameters": t.inputSchema or {"type": "object", "properties": {}}
                }
            }
            formatted_tools.append(tool_schema)
        return formatted_tools

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        # Strip the prefix e.g., 'splunk__splunk_run_query' -> 'splunk_run_query'
        actual_tool_name = tool_name.split("__", 1)[1]
        result = await self.session.call_tool(actual_tool_name, arguments)
        return result.content[0].text if result.content else ""


GLOBAL_DYNAMIC_CATALOG_CACHE = None

class IncidentCommander:
    def __init__(self, room_id: str, is_new_incident: bool = False):
        self.room_id = room_id
        self.is_new_incident = is_new_incident
        self.connections: Dict[str, MCPConnection] = {}
        self.dynamic_catalog: str = ""
        self.model = settings.ollama_model
        
        self.native_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_full_incident_transcript",
                    "description": "Fetches the full, raw historical chat transcript for the current incident room. Use this when asked to generate an RCA (Root Cause Analysis) so you have the entire context.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_to_incident_timeline",
                    "description": "Permanently saves an important discovery, fact, or IoC to the incident timeline so it is not forgotten.",
                    "parameters": {
                        "type": "object",
                        "properties": {"event": {"type": "string", "description": "The description of the event or fact to save."}},
                        "required": ["event"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_past_incidents",
                    "description": "Searches the database for similar past incidents, alerts, or tactics based on a keyword.",
                    "parameters": {
                        "type": "object",
                        "properties": {"keyword": {"type": "string", "description": "The tactic, technique, or keyword to search for (e.g. 'brute force')."}},
                        "required": ["keyword"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_virustotal",
                    "description": "Checks an IP address or domain against VirusTotal threat intelligence to see if it is malicious.",
                    "parameters": {
                        "type": "object",
                        "properties": {"indicator": {"type": "string", "description": "The IP address or domain name to scan."}},
                        "required": ["indicator"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_jira_issue",
                    "description": "Fetches the details (summary, description, status) of a specific Jira ticket by ID (e.g. SEC-123).",
                    "parameters": {
                        "type": "object",
                        "properties": {"issue_id": {"type": "string", "description": "The Jira ticket ID"}},
                        "required": ["issue_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_jira_issues",
                    "description": "Searches Jira tickets using JQL.",
                    "parameters": {
                        "type": "object",
                        "properties": {"jql": {"type": "string", "description": "The JQL query"}},
                        "required": ["jql"]
                    }
                }
            }
        ]
        self.tools_cache: List[dict] = list(self.native_tools)

    async def initialize_connections(self):
        """Dynamically loads MCP connections based on config."""
        # 1. Splunk
        if settings.splunk_mcp_url and settings.splunk_mcp_token:
            splunk_conn = MCPConnection(
                name="splunk",
                command="npx",
                args=[
                    "-y", "mcp-remote",
                    settings.splunk_mcp_url,
                    "--header", f"Authorization: Bearer {settings.splunk_mcp_token}"
                ]
            )
            await splunk_conn.connect()
            self.connections["splunk"] = splunk_conn
            self.tools_cache.extend(await splunk_conn.list_tools())

        # Jira is now handled purely natively via REST API using native tools!

        # Future integrations (Elastic, SumoLogic) would be added here
        
        # Self-Discover Capabilities
        await self._generate_dynamic_catalog()

    async def _generate_dynamic_catalog(self):
        """Uses LLM to automatically deduce capabilities from connected MCP tool schemas."""
        global GLOBAL_DYNAMIC_CATALOG_CACHE
        if self.is_new_incident:
            logger.info("New incident detected. Invalidating Dynamic Catalog Cache to refresh schemas.")
            GLOBAL_DYNAMIC_CATALOG_CACHE = None
            
        if GLOBAL_DYNAMIC_CATALOG_CACHE:
            self.dynamic_catalog = GLOBAL_DYNAMIC_CATALOG_CACHE
            return

        try:
            logger.info("Auto-discovering Data Catalog capabilities from tool schemas...")
            schemas = json.dumps([t["function"] for t in self.tools_cache], indent=2)
            
            prompt = f"""You are the WarRoom Data Cataloger. 
Analyze these raw MCP tool schemas and deduce what data integration they belong to and what they are best used for.
Return a concise summary mapping the integration names to their purpose (e.g. 'Splunk: Best for X, Y, Z. Jira: Best for A, B.'). 
Do not use markdown blocks. Return plain text instructions for an Incident Commander on when to use which tools.

Schemas:
{schemas[:4000]} # Truncated to avoid token bloat
"""
            
            model_str = self.model
            api_base_url = settings.llm_api_base
            if api_base_url and ".azure.com" in api_base_url:
                if not model_str.startswith("azure/"):
                    model_str = f"azure/{model_str}"
                api_base_url = api_base_url.replace("openai/v1/", "").rstrip("/")
                
            response = completion(
                model=model_str,
                messages=[{"role": "user", "content": prompt}],
                api_key=settings.llm_api_key or "mock",
                api_base=api_base_url if api_base_url else None,
                api_version="2024-02-15-preview" if "azure/" in model_str else None,
            )
            self.dynamic_catalog = response.choices[0].message.content
            GLOBAL_DYNAMIC_CATALOG_CACHE = self.dynamic_catalog
            logger.info(f"Generated Dynamic Catalog:\n{self.dynamic_catalog}")
        except Exception as e:
            logger.error(f"Failed to generate dynamic catalog: {e}")
            self.dynamic_catalog = "Dynamic Cataloger failed to analyze schemas."

    async def close(self):
        for conn in self.connections.values():
            await conn.disconnect()

    def _get_history(self) -> List[dict]:
        db = SessionLocal()
        try:
            messages = db.query(Message).filter(Message.room_id == self.room_id).order_by(Message.created_at.asc()).all()
            formatted = [{"role": m.role, "content": m.content} for m in messages if m.role in ["user", "assistant", "system"]]
            return formatted[-20:]
        finally:
            db.close()

    def _get_room_timeline(self) -> list:
        db = SessionLocal()
        try:
            room = db.query(Room).filter(Room.id == self.room_id).first()
            return room.timeline if room and room.timeline else []
        finally:
            db.close()

    def _add_to_timeline(self, event: str) -> str:
        db = SessionLocal()
        try:
            room = db.query(Room).filter(Room.id == self.room_id).first()
            if room:
                current = list(room.timeline) if room.timeline else []
                current.append(event)
                room.timeline = current
                db.commit()
                return f"Successfully added '{event}' to the incident timeline permanently."
            return "Error: Room not found."
        finally:
            db.close()

    def _get_full_incident_transcript(self) -> str:
        db = SessionLocal()
        try:
            messages = db.query(Message).filter(Message.room_id == self.room_id).order_by(Message.created_at.asc()).all()
            if not messages:
                return "No historical messages found for this incident."
            transcript = "\n".join([f"[{m.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {m.role.upper()}: {m.content}" for m in messages])
            return f"--- FULL INCIDENT TRANSCRIPT ---\n{transcript}\n--- END OF TRANSCRIPT ---"
        finally:
            db.close()

    def _search_past_incidents(self, keyword: str) -> str:
        db = SessionLocal()
        try:
            rooms = db.query(Room).filter(Room.id != self.room_id).all()
            matches = []
            keyword_lower = keyword.lower()
            for r in rooms:
                timeline_str = " ".join(r.timeline).lower() if r.timeline else ""
                title_str = r.title.lower() if r.title else ""
                if keyword_lower in title_str or keyword_lower in timeline_str:
                    matches.append(f"Incident '{r.title}' (ID: {r.id}, Severity: {r.severity}): {len(r.timeline) if r.timeline else 0} timeline events recorded. Excerpt: {timeline_str[:200]}...")
            
            if not matches:
                return f"No past incidents found matching keyword: '{keyword}'"
            
            return "Found similar incidents:\n" + "\n".join(matches)
            return "Found similar incidents:\n" + "\n".join(matches)
        finally:
            db.close()

    def _check_virustotal(self, indicator: str) -> str:
        if not settings.vt_api_key or settings.vt_api_key == "********":
            return "Error: VirusTotal API key is not configured in the Integrations tab."
        
        import urllib.request
        import urllib.error
        
        indicator = indicator.strip()
        is_ip = all(c.isdigit() or c == '.' for c in indicator)
        endpoint = "ip_addresses" if is_ip else "domains"
        
        url = f"https://www.virustotal.com/api/v3/{endpoint}/{indicator}"
        req = urllib.request.Request(url, headers={"x-apikey": settings.vt_api_key})
        
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                if malicious > 0:
                    return f"ALERT: {indicator} flagged as MALICIOUS by {malicious} security vendors on VirusTotal!"
                return f"SAFE: {indicator} is clean. 0 malicious detections."
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return f"VirusTotal: No data found for {indicator}"
            return f"VirusTotal Error: HTTP {e.code}"
        except Exception as e:
            return f"VirusTotal Error: {str(e)}"

    def _get_jira_issue(self, issue_id: str) -> str:
        if not settings.jira_mcp_url or not settings.jira_mcp_token:
            return "Error: Jira URL or token is not configured in the Integrations tab."
        
        import urllib.request
        import urllib.error
        import base64
        import json
        
        jira_url = settings.jira_mcp_url.rstrip('/')
        if not jira_url.startswith("http"):
            jira_url = f"https://{jira_url}"
        url = f"{jira_url}/rest/api/3/issue/{issue_id}"
        
        auth_bytes = settings.jira_mcp_token.encode('utf-8')
        base64_auth = base64.b64encode(auth_bytes).decode('utf-8')
        
        req = urllib.request.Request(url, headers={
            "Authorization": f"Basic {base64_auth}",
            "Accept": "application/json"
        })
        
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                summary = data.get("fields", {}).get("summary", "No Summary")
                status = data.get("fields", {}).get("status", {}).get("name", "Unknown")
                desc = data.get("fields", {}).get("description", {})
                
                # Extract text from ADF if present
                desc_text = ""
                if isinstance(desc, dict) and desc.get("type") == "doc":
                    for block in desc.get("content", []):
                        for text_node in block.get("content", []):
                            if text_node.get("type") == "text":
                                desc_text += text_node.get("text", "") + " "
                elif isinstance(desc, str):
                    desc_text = desc
                    
                desc_text = desc_text[:1000] + "..." if len(desc_text) > 1000 else desc_text
                
                return f"Jira Ticket {issue_id}: {summary}\nStatus: {status}\nDescription: {desc_text}"
        except Exception as e:
            return f"Jira Error fetching {issue_id}: {str(e)}"

    def _search_jira_issues(self, jql: str) -> str:
        if not settings.jira_mcp_url or not settings.jira_mcp_token:
            return "Error: Jira URL or token is not configured in the Integrations tab."
        
        import urllib.request
        import urllib.parse
        import urllib.error
        import base64
        import json
        
        jira_url = settings.jira_mcp_url.rstrip('/')
        if not jira_url.startswith("http"):
            jira_url = f"https://{jira_url}"
            
        jql_encoded = urllib.parse.quote(jql)
        url = f"{jira_url}/rest/api/3/search/jql?jql={jql_encoded}&maxResults=10&fields=summary,status"
        
        auth_bytes = settings.jira_mcp_token.encode('utf-8')
        base64_auth = base64.b64encode(auth_bytes).decode('utf-8')
        
        req = urllib.request.Request(url, headers={
            "Authorization": f"Basic {base64_auth}",
            "Accept": "application/json"
        })
        
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                issues = data.get("issues", [])
                if not issues:
                    return f"No Jira issues found matching JQL: {jql}"
                
                result = [f"Found {len(issues)} issues matching '{jql}':"]
                for i in issues:
                    key = i.get("key")
                    summary = i.get("fields", {}).get("summary", "")
                    status = i.get("fields", {}).get("status", {}).get("name", "")
                    result.append(f"- {key}: {summary} ({status})")
                return "\n".join(result)
        except Exception as e:
            return f"Jira Search Error: {str(e)}"

    def _save_message(self, role: str, content: str):
        db = SessionLocal()
        try:
            msg = Message(room_id=self.room_id, role=role, content=content)
            db.add(msg)
            db.commit()
        finally:
            db.close()

    async def run(self, user_prompt: str, system_prompt: str = None) -> str:
        """Runs the main LLM loop with tool calling."""
        if not self.connections:
            await self.initialize_connections()

        self._save_message("user", user_prompt)
        
        messages = []
        timeline = self._get_room_timeline()
        timeline_text = "- " + "\n- ".join(timeline) if timeline else "No events recorded yet."
        
        splunk_status = "Connected" if "splunk" in self.connections else "Not connected. DO NOT hallucinate Splunk queries. If the user asks for Splunk data, tell them Splunk MCP is not configured."
        jira_status = "Connected (Native REST API)" if settings.jira_mcp_url and settings.jira_mcp_token else "Not connected. DO NOT try to read Jira tickets."
        
        catalog_text = "### SELF-DISCOVERED DATA CATALOG INTELLIGENCE ###\n"
        catalog_text += "You must consult this auto-generated catalog to determine WHICH tools to use before acting.\n"
        catalog_text += f"{self.dynamic_catalog}\n\n"

        system_base = f"You are the WarRoom Incident Commander.\n" \
                      f"You lead a team of specialized parallel subagents (Splunk, VirusTotal, Jira). " \
                      f"CRITICAL: When investigating an incident, you MUST deploy your subagents CONCURRENTLY. If you need data from Splunk, VT, and Jira, invoke all their tools simultaneously in a single turn to parallelize the investigation. Do not wait for one tool to finish before calling another.\n" \
                      f"CRITICAL COMMUNICATION STYLE: Respond naturally like an elite human commander in a chat room. DO NOT use rigid bulleted lists like 'Actions performed'. Speak directly and decisively.\n\n" \
                      f"{catalog_text}" \
                      f"FORMATTING RULES:\n" \
                      f"- When asked to generate an RCA (Root Cause Analysis), use a highly structured, professional incident report format. Include sections like: 🚨 Executive Summary, 🔍 Root Cause, ⏱️ Attack Timeline, 🛡️ Impact & Indicators, and 🛠️ Remediation.\n" \
                      f"- When outputting VirusTotal results, heavily decorate the output using Slack markdown to make it pop. Use *bold* for malicious counts, _italics_ for context, and emojis (🚨, ✅, ⚠️).\n\n" \
                      f"Current Integration Status:\n" \
                      f"- Splunk: {splunk_status}\n" \
                      f"- Jira: {jira_status}\n\n" \
                      f"You only have access to the last 20 chat messages in your memory window. " \
                      f"If the user mentions an IP address or domain, or you discover one in logs, you MUST immediately use the `check_virustotal` tool to scan it.\n" \
                      f"If you discover a critical Indicator of Compromise (IoC) or an important fact, you MUST use the `add_to_incident_timeline` tool to save it permanently. " \
                      f"Current Incident Timeline:\n{timeline_text}"

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt + "\n\n" + system_base})
        else:
            messages.append({"role": "system", "content": system_base})

        messages.extend(self._get_history())
        
        active_tools = self.tools_cache
        
        max_iterations = 5
        for _ in range(max_iterations):
            try:
                model_str = self.model
                api_base_url = settings.llm_api_base
                
                # Auto-detect Azure from the base URL so the user doesn't have to type azure/
                if api_base_url and ".azure.com" in api_base_url:
                    if not model_str.startswith("azure/"):
                        model_str = f"azure/{model_str}"
                    # LiteLLM Azure expects the base URL without /openai/v1/
                    api_base_url = api_base_url.replace("openai/v1/", "").rstrip("/")
                    
                response = completion(
                    model=model_str,
                    messages=messages,
                    tools=active_tools,
                    api_key=settings.llm_api_key or "mock",
                    api_base=api_base_url if api_base_url else None,
                    api_version="2024-02-15-preview" if "azure/" in model_str else None,
                )
            except Exception as e:
                logger.error(f"LLM Error: {e}")
                return f"Error contacting LLM: {e}"

            response_message = response.choices[0].message
            messages.append(response_message)

            if not response_message.tool_calls:
                # LLM provided a final text answer
                final_text = response_message.content
                if not final_text or not final_text.strip():
                    final_text = "⚠️ **Model Output Error**: The AI returned an empty response. This usually happens when local/smaller models get confused by the complex Splunk/Jira tool schemas. For the best experience, please configure a stronger model (like `gpt-4o` or `claude-3-5-sonnet`) in the Integrations tab!"
                self._save_message("assistant", final_text)
                return final_text

            # Execute tool calls concurrently
            async def execute_tool(tool_call):
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                logger.info(f"SubAgent dispatched for: {function_name} with args {arguments}")
                
                prefix = function_name.split("__")[0]
                tool_result = "Error: Tool execution failed or unknown tool."
                
                if function_name == "add_to_incident_timeline":
                    tool_result = self._add_to_timeline(arguments.get("event", ""))
                elif function_name == "get_full_incident_transcript":
                    tool_result = self._get_full_incident_transcript()
                elif function_name == "search_past_incidents":
                    tool_result = self._search_past_incidents(arguments.get("keyword", ""))
                elif function_name == "check_virustotal":
                    tool_result = self._check_virustotal(arguments.get("indicator", ""))
                elif function_name == "get_jira_issue":
                    tool_result = self._get_jira_issue(arguments.get("issue_id", ""))
                elif function_name == "search_jira_issues":
                    tool_result = self._search_jira_issues(arguments.get("jql", ""))
                elif prefix in self.connections:
                    try:
                        tool_result = await self.connections[prefix].call_tool(function_name, arguments)
                    except Exception as e:
                        tool_result = f"Error executing tool {function_name}: {str(e)}"
                
                return {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": tool_result
                }

            # Map-Reduce: Dispatch all tools (subagents) at once and gather results
            tool_results = await asyncio.gather(*(execute_tool(tc) for tc in response_message.tool_calls))
            messages.extend(tool_results)

        final_msg = "Investigation timed out after maximum tool iterations."
        self._save_message("assistant", final_msg)
        return final_msg
