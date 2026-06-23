"""
DATA CATALOG
This file defines the Intelligence Layer for the WarRoom AI Incident Commander.
It maps integrations to their specific capabilities, preventing the LLM from 
hallucinating queries against the wrong systems and optimizing API usage.
"""

DATA_CATALOG = {
    "splunk": {
        "description": "Primary SIEM. Contains network traffic, firewall logs, Windows Event Logs, Active Directory authentication logs, and DNS telemetry.",
        "best_for": ["lateral movement", "brute force", "data exfiltration", "network anomalies", "authentication failures"],
        "instructions": "If the user asks to check network logs, firewall blocks, or authentication failures, you MUST use the Splunk tools."
    },
    "virustotal": {
        "description": "Global threat intelligence feed.",
        "best_for": ["IP reputation", "malware hashes", "suspicious domains"],
        "instructions": "If you discover an IP address, domain, or hash, you MUST use VirusTotal to verify its reputation."
    },
    "jira": {
        "description": "ITSM Ticketing System.",
        "best_for": ["past incidents", "remediation tracking", "ticket status"],
        "instructions": "If the user asks about an existing ticket (e.g. SEC-123) or past resolved incidents logged by engineers, use Jira."
    },
    "database_memory": {
        "description": "Internal WarRoom Historical Incident Memory.",
        "best_for": ["Root Cause Analysis (RCA)", "incident timelines", "past similar alerts in WarRoom"],
        "instructions": "If the user asks for an RCA or an incident transcript, use the 'get_full_incident_transcript' tool. If they ask about similar past alerts, use 'search_past_incidents'."
    }
}
