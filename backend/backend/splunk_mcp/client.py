"""
WarRoom – Splunk MCP Client
===========================
Wraps connectivity to the Splunk MCP Server (CiscoDevNet/Splunk-MCP-Server-official)
with automatic fallback to the splunk-sdk REST API and a comprehensive demo-data mode.

Usage::

    client = SplunkMCPClient(settings)
    await client.connect()
    results = await client.run_query('index=botsv1 | head 5')
    await client.disconnect()
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import sys
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger("warroom.splunk_mcp")

# ---------------------------------------------------------------------------
# Try to import optional SDK dependencies – they may not be installed in
# demo-only environments.
# ---------------------------------------------------------------------------
try:
    # Disable MCP import because it hangs Python 3.13 on this environment
    # from mcp import ClientSession, StdioServerParameters
    # from mcp.client.stdio import stdio_client

    _MCP_AVAILABLE = False
except ImportError:
    _MCP_AVAILABLE = False
    logger.info("mcp SDK not installed – MCP transport unavailable")

try:
    import splunklib.client as splunk_client_lib
    import splunklib.results as splunk_results_lib

    _SPLUNK_SDK_AVAILABLE = True
except ImportError:
    _SPLUNK_SDK_AVAILABLE = False
    logger.info("splunk-sdk not installed – REST API fallback unavailable")


class SplunkMCPClient:
    """
    Unified Splunk query client.

    Connection priority:
    1. **MCP Server** (stdio transport) – preferred when ``splunk_mcp_server_path`` is set.
    2. **splunk-sdk REST API** – fallback when MCP is unavailable.
    3. **Demo mode** – returns realistic synthetic data; no Splunk instance needed.
    """

    def __init__(self, settings: Any) -> None:
        self._settings = settings
        self._mcp_session: Optional[Any] = None
        self._mcp_context: Optional[Any] = None
        self._splunk_service: Optional[Any] = None
        self._transport: str = "none"  # 'mcp', 'rest', 'demo'

    # ── lifecycle ──────────────────────────────────────────────────────

    async def connect(self) -> str:
        """
        Establish the best available connection and return the transport name.
        """
        if self._settings.demo_mode:
            self._transport = "demo"
            logger.info("Running in DEMO mode – synthetic data will be used")
            return self._transport

        # Attempt 1: MCP stdio transport
        if _MCP_AVAILABLE and self._settings.splunk_mcp_server_path:
            try:
                await self._connect_mcp()
                self._transport = "mcp"
                logger.info("Connected via MCP stdio transport")
                return self._transport
            except Exception as exc:
                logger.warning("MCP connection failed (%s), trying REST fallback", exc)

        # Attempt 2: splunk-sdk REST
        if _SPLUNK_SDK_AVAILABLE and self._settings.splunk_token:
            try:
                self._connect_rest()
                self._transport = "rest"
                logger.info("Connected via splunk-sdk REST API")
                return self._transport
            except Exception as exc:
                logger.warning("REST connection failed (%s), falling back to demo", exc)

        # Attempt 3: demo
        self._transport = "demo"
        logger.info("No live Splunk available – falling back to DEMO mode")
        return self._transport

    async def disconnect(self) -> None:
        """Cleanly close any open sessions."""
        if self._mcp_session:
            try:
                await self._mcp_session.__aexit__(None, None, None)
            except Exception:
                pass
            self._mcp_session = None
        self._splunk_service = None
        self._transport = "none"

    # ── MCP transport ──────────────────────────────────────────────────

    async def _connect_mcp(self) -> None:
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[self._settings.splunk_mcp_server_path],
            env={
                "SPLUNK_HOST": self._settings.splunk_host,
                "SPLUNK_PORT": str(self._settings.splunk_port),
                "SPLUNK_TOKEN": self._settings.splunk_token,
                "SPLUNK_SCHEME": self._settings.splunk_scheme,
            },
        )
        # stdio_client is an async context-manager that yields (read, write)
        self._mcp_context = stdio_client(server_params)
        read_stream, write_stream = await self._mcp_context.__aenter__()
        self._mcp_session = ClientSession(read_stream, write_stream)
        await self._mcp_session.__aenter__()
        await self._mcp_session.initialize()

    async def _mcp_call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call an MCP tool and return the parsed result."""
        assert self._mcp_session is not None
        result = await self._mcp_session.call_tool(tool_name, arguments=arguments)
        # MCP returns content blocks; concatenate text blocks and try to parse as JSON
        texts = [block.text for block in result.content if hasattr(block, "text")]
        raw = "\n".join(texts)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    # ── REST transport ─────────────────────────────────────────────────

    def _connect_rest(self) -> None:
        self._splunk_service = splunk_client_lib.connect(
            host=self._settings.splunk_host,
            port=int(self._settings.splunk_port),
            token=self._settings.splunk_token,
            scheme=self._settings.splunk_scheme,
            autologin=True,
        )

    def _rest_search(self, spl_query: str, earliest: str, latest: str) -> list[dict[str, Any]]:
        """Blocking search via splunk-sdk.  Called inside ``run_in_executor``."""
        assert self._splunk_service is not None
        kwargs = {
            "earliest_time": earliest,
            "latest_time": latest,
            "search_mode": "normal",
            "output_mode": "json",
            "count": 500,
        }
        if not spl_query.strip().startswith("|"):
            spl_query = f"search {spl_query}"
        job = self._splunk_service.jobs.create(spl_query, **kwargs)
        while not job.is_done():
            import time
            time.sleep(0.5)
        reader = splunk_results_lib.JSONResultsReader(job.results(output_mode="json"))
        rows: list[dict[str, Any]] = []
        for item in reader:
            if isinstance(item, dict):
                rows.append(item)
        job.cancel()
        return rows

    # ── public API ─────────────────────────────────────────────────────

    async def run_query(
        self,
        spl_query: str,
        earliest: str = "-24h",
        latest: str = "now",
    ) -> list[dict[str, Any]]:
        """
        Execute an SPL query and return a list of result dicts.
        """
        logger.info("run_query [%s]: %s", self._transport, spl_query[:120])

        if self._transport == "mcp":
            return await self._mcp_call_tool(
                "splunk_run_query",
                {"search_query": spl_query, "earliest_time": earliest, "latest_time": latest},
            )

        if self._transport == "rest":
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._rest_search, spl_query, earliest, latest)

        # Demo mode
        return self._demo_query(spl_query)

    async def get_indexes(self) -> list[str]:
        if self._transport == "mcp":
            return await self._mcp_call_tool("splunk_list_indexes", {})
        if self._transport == "rest":
            assert self._splunk_service is not None
            return [idx.name for idx in self._splunk_service.indexes.list()]
        return ["botsv1", "main", "summary", "_internal", "_audit"]

    async def get_metadata(self, index: str = "botsv1") -> dict[str, Any]:
        if self._transport == "mcp":
            return await self._mcp_call_tool("splunk_get_index_metadata", {"index_name": index})
        return {
            "index": index,
            "totalEventCount": 28_434_212 if index == "botsv1" else 0,
            "currentDBSizeMB": 4_321,
            "minTime": "2016-08-10T00:00:00.000+00:00",
            "maxTime": "2016-08-12T23:59:59.000+00:00",
        }

    async def get_saved_searches(self) -> list[dict[str, Any]]:
        if self._transport == "mcp":
            return await self._mcp_call_tool("splunk_list_saved_searches", {})
        if self._transport == "rest":
            assert self._splunk_service is not None
            return [
                {"name": ss.name, "search": ss["search"]}
                for ss in self._splunk_service.saved_searches.list()
            ]
        return [
            {"name": "WarRoom - Brute Force Detection", "search": "index=botsv1 EventCode=4625 | stats count by src_ip"},
            {"name": "WarRoom - Lateral Movement", "search": "index=botsv1 | stats dc(dest_ip) by src_ip | where dc > 5"},
        ]

    # ── demo data ──────────────────────────────────────────────────────

    def _demo_query(self, spl_query: str) -> list[dict[str, Any]]:
        """
        Return realistic synthetic data based on the SPL query keywords.
        """
        q = spl_query.lower()

        # ── brute force ────────────────────────────────────────────────
        if "4625" in q or "brute" in q:
            return self._demo_brute_force(q)
        if "4624" in q and "4625" in q:
            return self._demo_login_sequence(q)

        # ── lateral movement ───────────────────────────────────────────
        if "dc(dest" in q or "lateral" in q or "unique_dests" in q:
            return self._demo_lateral_movement(q)

        # ── data exfiltration ──────────────────────────────────────────
        if "bytes_out" in q or "exfil" in q:
            return self._demo_exfiltration(q)

        # ── DNS ────────────────────────────────────────────────────────
        if "dns" in q:
            return self._demo_dns(q)

        # ── web attacks ────────────────────────────────────────────────
        if "http" in q or "uri_path" in q or "attack_pattern" in q:
            return self._demo_web_attacks(q)

        # ── firewall ──────────────────────────────────────────────────
        if "firewall" in q or "blocked" in q:
            return self._demo_firewall(q)

        # ── geo ────────────────────────────────────────────────────────
        if "iplocation" in q or "geo" in q or "country" in q:
            return self._demo_geo(q)

        # ── user activity ─────────────────────────────────────────────
        if "user=" in q and "stats count by sourcetype" in q:
            return self._demo_user_activity(q)

        # ── ip activity summary ───────────────────────────────────────
        if "stats count by sourcetype" in q:
            return self._demo_ip_activity(q)

        # ── timeline ──────────────────────────────────────────────────
        if "sort _time" in q and "table _time" in q:
            return self._demo_timeline(q)

        # ── notable events ────────────────────────────────────────────
        if "notable" in q:
            return self._demo_notable()

        # ── generic fallback ──────────────────────────────────────────
        return self._demo_generic(q)

    # -- demo data generators -------------------------------------------

    @staticmethod
    def _base_time() -> datetime:
        return datetime.utcnow() - timedelta(hours=2)

    def _demo_brute_force(self, q: str) -> list[dict[str, Any]]:
        base = self._base_time()
        return [
            {"user": "admin", "src_ip": "203.0.113.50", "count": "87"},
            {"user": "root", "src_ip": "203.0.113.50", "count": "52"},
            {"user": "svc_backup", "src_ip": "203.0.113.50", "count": "23"},
            {"user": "jsmith", "src_ip": "203.0.113.50", "count": "15"},
            {"user": "administrator", "src_ip": "203.0.113.50", "count": "11"},
        ]

    def _demo_login_sequence(self, q: str) -> list[dict[str, Any]]:
        base = self._base_time()
        events = []
        # Many failures followed by a success
        for i in range(8):
            events.append({
                "_time": (base + timedelta(seconds=i * 3)).isoformat() + "Z",
                "EventCode": "4625",
                "user": "admin",
                "src_ip": "203.0.113.50",
            })
        events.append({
            "_time": (base + timedelta(seconds=30)).isoformat() + "Z",
            "EventCode": "4624",
            "user": "admin",
            "src_ip": "203.0.113.50",
        })
        return events

    def _demo_lateral_movement(self, q: str) -> list[dict[str, Any]]:
        return [
            {
                "src_ip": "203.0.113.50",
                "unique_dests": "7",
                "destinations": [
                    "192.0.2.10", "192.0.2.11", "192.0.2.12",
                    "192.0.2.20", "192.0.2.21", "192.0.2.30", "192.0.2.31",
                ],
            }
        ]

    def _demo_exfiltration(self, q: str) -> list[dict[str, Any]]:
        return [
            {"src_ip": "192.0.2.10", "dest_ip": "198.51.100.77", "total_bytes_out": "524288000"},
            {"src_ip": "192.0.2.10", "dest_ip": "198.51.100.200", "total_bytes_out": "157286400"},
            {"src_ip": "192.0.2.11", "dest_ip": "203.0.113.99", "total_bytes_out": "52428800"},
        ]

    def _demo_dns(self, q: str) -> list[dict[str, Any]]:
        return [
            {"query_type": "A", "count": "342", "avg_query_len": "24.5"},
            {"query_type": "TXT", "count": "189", "avg_query_len": "127.3"},
            {"query_type": "AAAA", "count": "56", "avg_query_len": "22.1"},
            {"query_type": "MX", "count": "12", "avg_query_len": "31.0"},
            {"query_type": "CNAME", "count": "8", "avg_query_len": "28.7"},
        ]

    def _demo_web_attacks(self, q: str) -> list[dict[str, Any]]:
        base = self._base_time()
        return [
            {
                "_time": (base + timedelta(minutes=0)).isoformat() + "Z",
                "src_ip": "203.0.113.50",
                "uri_path": "/login.php?id=1' UNION SELECT username,password FROM users--",
                "attack_pattern": "union",
            },
            {
                "_time": (base + timedelta(minutes=1)).isoformat() + "Z",
                "src_ip": "203.0.113.50",
                "uri_path": "/search?q=<script>alert(document.cookie)</script>",
                "attack_pattern": "script",
            },
            {
                "_time": (base + timedelta(minutes=2)).isoformat() + "Z",
                "src_ip": "203.0.113.50",
                "uri_path": "/admin/exec.php?cmd=eval(base64_decode('...'))",
                "attack_pattern": "eval",
            },
            {
                "_time": (base + timedelta(minutes=3)).isoformat() + "Z",
                "src_ip": "203.0.113.50",
                "uri_path": "/api/users?filter=1;SELECT * FROM credentials",
                "attack_pattern": "select",
            },
        ]

    def _demo_firewall(self, q: str) -> list[dict[str, Any]]:
        return [
            {"dest_ip": "192.0.2.10", "dest_port": "22", "count": "145"},
            {"dest_ip": "192.0.2.11", "dest_port": "3389", "count": "89"},
            {"dest_ip": "192.0.2.12", "dest_port": "445", "count": "67"},
            {"dest_ip": "192.0.2.20", "dest_port": "8080", "count": "34"},
            {"dest_ip": "192.0.2.30", "dest_port": "1433", "count": "23"},
        ]

    def _demo_geo(self, q: str) -> list[dict[str, Any]]:
        return [
            {"Country": "Russia", "City": "Moscow", "Region": "Moscow Oblast", "count": "312"},
            {"Country": "China", "City": "Beijing", "Region": "Beijing", "count": "89"},
            {"Country": "Netherlands", "City": "Amsterdam", "Region": "North Holland", "count": "45"},
        ]

    def _demo_user_activity(self, q: str) -> list[dict[str, Any]]:
        return [
            {"sourcetype": "WinEventLog:Security", "action": "failure", "count": "87"},
            {"sourcetype": "WinEventLog:Security", "action": "success", "count": "3"},
            {"sourcetype": "stream:http", "action": "allowed", "count": "234"},
            {"sourcetype": "stream:dns", "action": "allowed", "count": "156"},
            {"sourcetype": "syslog", "action": "info", "count": "42"},
        ]

    def _demo_ip_activity(self, q: str) -> list[dict[str, Any]]:
        return [
            {"sourcetype": "stream:http", "count": "1245"},
            {"sourcetype": "WinEventLog:Security", "count": "398"},
            {"sourcetype": "stream:dns", "count": "342"},
            {"sourcetype": "firewall", "count": "267"},
            {"sourcetype": "stream:tcp", "count": "189"},
            {"sourcetype": "syslog", "count": "56"},
        ]

    def _demo_timeline(self, q: str) -> list[dict[str, Any]]:
        base = self._base_time()
        timeline = [
            {"_time": (base + timedelta(minutes=0)).isoformat() + "Z", "sourcetype": "firewall", "action": "allowed", "src_ip": "203.0.113.50", "dest_ip": "192.0.2.10", "user": "", "url": ""},
            {"_time": (base + timedelta(minutes=1)).isoformat() + "Z", "sourcetype": "stream:dns", "action": "allowed", "src_ip": "203.0.113.50", "dest_ip": "192.0.2.1", "user": "", "url": "imreallynotmalware.com"},
            {"_time": (base + timedelta(minutes=2)).isoformat() + "Z", "sourcetype": "WinEventLog:Security", "action": "failure", "src_ip": "203.0.113.50", "dest_ip": "192.0.2.10", "user": "admin", "url": ""},
            {"_time": (base + timedelta(minutes=3)).isoformat() + "Z", "sourcetype": "WinEventLog:Security", "action": "failure", "src_ip": "203.0.113.50", "dest_ip": "192.0.2.10", "user": "admin", "url": ""},
            {"_time": (base + timedelta(minutes=5)).isoformat() + "Z", "sourcetype": "WinEventLog:Security", "action": "success", "src_ip": "203.0.113.50", "dest_ip": "192.0.2.10", "user": "admin", "url": ""},
            {"_time": (base + timedelta(minutes=6)).isoformat() + "Z", "sourcetype": "stream:http", "action": "allowed", "src_ip": "192.0.2.10", "dest_ip": "192.0.2.11", "user": "admin", "url": "/admin/config"},
            {"_time": (base + timedelta(minutes=8)).isoformat() + "Z", "sourcetype": "stream:http", "action": "allowed", "src_ip": "192.0.2.10", "dest_ip": "192.0.2.12", "user": "admin", "url": "/api/data/export"},
            {"_time": (base + timedelta(minutes=10)).isoformat() + "Z", "sourcetype": "stream:tcp", "action": "allowed", "src_ip": "192.0.2.10", "dest_ip": "198.51.100.77", "user": "admin", "url": ""},
        ]
        return timeline

    def _demo_notable(self) -> list[dict[str, Any]]:
        base = self._base_time()
        return [
            {"rule_name": "Brute Force - Excessive Failed Logins", "severity": "high", "src": "203.0.113.50", "dest": "192.0.2.10", "user": "admin", "_time": (base - timedelta(hours=1)).isoformat() + "Z"},
            {"rule_name": "Lateral Movement - Multiple Host Access", "severity": "critical", "src": "192.0.2.10", "dest": "192.0.2.11", "user": "admin", "_time": (base - timedelta(minutes=45)).isoformat() + "Z"},
            {"rule_name": "Data Exfiltration - Large Outbound Transfer", "severity": "critical", "src": "192.0.2.10", "dest": "198.51.100.77", "user": "admin", "_time": (base - timedelta(minutes=30)).isoformat() + "Z"},
            {"rule_name": "Suspicious DNS - Potential Tunneling", "severity": "medium", "src": "192.0.2.20", "dest": "192.0.2.1", "user": "svc_dns", "_time": (base - timedelta(minutes=20)).isoformat() + "Z"},
            {"rule_name": "Web Attack - SQL Injection Attempt", "severity": "high", "src": "203.0.113.50", "dest": "192.0.2.30", "user": "", "_time": (base - timedelta(minutes=10)).isoformat() + "Z"},
        ]

    def _demo_generic(self, q: str) -> list[dict[str, Any]]:
        """Fallback for any unmatched query in demo mode."""
        base = self._base_time()
        return [
            {
                "_time": (base + timedelta(minutes=i)).isoformat() + "Z",
                "sourcetype": random.choice(["WinEventLog:Security", "stream:http", "syslog", "firewall"]),
                "src_ip": "203.0.113.50",
                "dest_ip": f"192.0.2.{10 + i}",
                "action": random.choice(["allowed", "blocked", "failure", "success"]),
                "count": str(random.randint(1, 50)),
            }
            for i in range(5)
        ]


# ── Demo alert generator (used by main.py when DEMO_MODE=true) ────────

def generate_demo_alerts() -> list[dict[str, Any]]:
    """
    Return a set of realistic pre-canned security alerts for the demo dashboard.
    Uses RFC 5737 IP ranges (192.0.2.x, 198.51.100.x, 203.0.113.x).
    """
    now = datetime.utcnow()
    return [
        {
            "id": "ALERT-001",
            "title": "Brute Force SSH Attack Detected",
            "severity": "high",
            "source_ip": "203.0.113.50",
            "dest_ip": "192.0.2.10",
            "user": "admin",
            "timestamp": (now - timedelta(hours=2, minutes=15)).isoformat() + "Z",
            "description": (
                "87 failed SSH login attempts detected from 203.0.113.50 targeting the 'admin' account "
                "on server 192.0.2.10 within a 5-minute window. The source IP is geolocated to Moscow, Russia. "
                "A successful login was observed 30 seconds after the last failure."
            ),
            "status": "new",
            "attack_type": "brute_force",
            "raw_event": {
                "EventCode": "4625",
                "TargetUserName": "admin",
                "IpAddress": "203.0.113.50",
                "LogonType": "10",
                "WorkstationName": "WEB-SVR-01",
            },
        },
        {
            "id": "ALERT-002",
            "title": "Lateral Movement – Multiple Internal Hosts Accessed",
            "severity": "critical",
            "source_ip": "192.0.2.10",
            "dest_ip": "192.0.2.11",
            "user": "admin",
            "timestamp": (now - timedelta(hours=1, minutes=45)).isoformat() + "Z",
            "description": (
                "Host 192.0.2.10 (WEB-SVR-01) initiated connections to 7 unique internal hosts within "
                "10 minutes using the 'admin' account. Protocols include SMB (445), RDP (3389), and WinRM (5985). "
                "This pattern is consistent with credential-based lateral movement."
            ),
            "status": "new",
            "attack_type": "lateral_movement",
            "raw_event": {
                "src_ip": "192.0.2.10",
                "unique_destinations": 7,
                "protocols": ["SMB", "RDP", "WinRM"],
            },
        },
        {
            "id": "ALERT-003",
            "title": "Large Data Exfiltration to External Host",
            "severity": "critical",
            "source_ip": "192.0.2.10",
            "dest_ip": "198.51.100.77",
            "user": "admin",
            "timestamp": (now - timedelta(hours=1, minutes=30)).isoformat() + "Z",
            "description": (
                "Host 192.0.2.10 transferred 524 MB of data to external IP 198.51.100.77 over HTTPS. "
                "The destination IP is associated with a VPS provider and has no prior legitimate traffic history. "
                "Transfer occurred outside business hours (02:30 UTC)."
            ),
            "status": "new",
            "attack_type": "data_exfiltration",
            "raw_event": {
                "src_ip": "192.0.2.10",
                "dest_ip": "198.51.100.77",
                "bytes_out": 524288000,
                "protocol": "HTTPS",
                "dest_port": 443,
            },
        },
        {
            "id": "ALERT-004",
            "title": "Suspicious DNS Activity – Potential DNS Tunneling",
            "severity": "medium",
            "source_ip": "192.0.2.20",
            "dest_ip": "192.0.2.1",
            "user": "svc_dns",
            "timestamp": (now - timedelta(hours=1, minutes=10)).isoformat() + "Z",
            "description": (
                "Host 192.0.2.20 generated 189 TXT DNS queries with an average query length of 127 characters "
                "within a 15-minute window. The queries were directed at subdomain patterns consistent with "
                "DNS tunneling (e.g., base64-encoded payloads in subdomain labels of tunnel.evil-c2.example.com)."
            ),
            "status": "new",
            "attack_type": "dns_tunneling",
            "raw_event": {
                "src_ip": "192.0.2.20",
                "query_type": "TXT",
                "avg_query_length": 127.3,
                "domain": "tunnel.evil-c2.example.com",
            },
        },
        {
            "id": "ALERT-005",
            "title": "Web Application Attack – SQL Injection Attempts",
            "severity": "high",
            "source_ip": "203.0.113.50",
            "dest_ip": "192.0.2.30",
            "user": None,
            "timestamp": (now - timedelta(minutes=45)).isoformat() + "Z",
            "description": (
                "Multiple SQL injection attempts detected from 203.0.113.50 targeting web application "
                "on 192.0.2.30:8080. Attack patterns include UNION SELECT, blind boolean-based injection, "
                "and time-based injection. 4 unique attack payloads identified across login.php, search, and API endpoints."
            ),
            "status": "new",
            "attack_type": "web_attack",
            "raw_event": {
                "src_ip": "203.0.113.50",
                "dest_ip": "192.0.2.30",
                "dest_port": 8080,
                "attack_patterns": ["UNION SELECT", "boolean-based blind", "time-based blind"],
                "http_status": [200, 500, 403],
            },
        },
        {
            "id": "ALERT-006",
            "title": "Privilege Escalation – Service Account Anomaly",
            "severity": "high",
            "source_ip": "192.0.2.12",
            "dest_ip": "192.0.2.12",
            "user": "svc_backup",
            "timestamp": (now - timedelta(minutes=30)).isoformat() + "Z",
            "description": (
                "Service account 'svc_backup' executed interactive logon on 192.0.2.12 (DB-SVR-01) "
                "and subsequently ran 'net localgroup administrators svc_backup /add'. "
                "This account has never performed interactive logons historically."
            ),
            "status": "new",
            "attack_type": "privilege_escalation",
            "raw_event": {
                "user": "svc_backup",
                "EventCode": "4732",
                "command": "net localgroup administrators svc_backup /add",
                "LogonType": "2",
            },
        },
    ]
