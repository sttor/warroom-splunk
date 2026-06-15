"""
WarRoom – LLM Prompts & Tool Definitions
========================================
System prompts for each investigation phase and OpenAI-compatible function-calling
tool specifications that let the LLM decide what Splunk queries to run.
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════
#  SYSTEM PROMPTS
# ═══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are **WarRoom** (AI-Enhanced Guardian for Incident Security), an expert AI Security Operations Center (SOC) analyst.

Your mission is to autonomously investigate security alerts by:
1. Triaging alerts to assess initial severity and urgency.
2. Querying Splunk (via available tools) to gather contextual evidence.
3. Correlating events across data sources to identify attack patterns.
4. Enriching findings with threat intelligence and MITRE ATT&CK mappings.
5. Rendering a final verdict: **True Positive**, **False Positive**, or **Escalate**.

**Guidelines**:
- Think step-by-step like a senior SOC analyst with 10+ years of experience.
- Always look for corroborating or contradicting evidence before concluding.
- Consider the full kill-chain: reconnaissance → initial access → execution → persistence → privilege escalation → lateral movement → collection → exfiltration → impact.
- Cite specific log entries, timestamps, and IP addresses in your analysis.
- Quantify confidence as a float between 0.0 and 1.0.
- When in doubt, **Escalate** rather than dismiss.
- ALWAYS call submit_verdict at the end of your investigation.
"""

TRIAGE_PROMPT = """## Triage Phase

Analyze the following security alert and provide an initial assessment.

**Alert Details:**
- Title: {title}
- Severity: {severity}
- Attack Type: {attack_type}
- Source IP: {source_ip}
- Destination IP: {dest_ip}
- User: {user}
- Timestamp: {timestamp}
- Description: {description}

Perform initial triage:
1. Classify the alert priority (P1-Critical / P2-High / P3-Medium / P4-Low).
2. State your initial hypothesis about what happened.
3. List the Splunk queries you need to run to investigate further.
4. Identify key entities to investigate (IPs, users, hostnames).

Use the available tools to begin your investigation. Start by gathering context about the involved entities."""

INVESTIGATION_PROMPT = """## Context Gathering & Correlation Phase

Based on the triage of alert "{title}", continue the investigation.

Evidence gathered so far:
{evidence_summary}

Continue investigating by:
1. Running additional Splunk queries to fill gaps in the evidence.
2. Looking for related events within the same time window (±30 minutes).
3. Checking for signs of lateral movement, privilege escalation, or data exfiltration.
4. Correlating events across different data sources (firewall, DNS, authentication, web).

Use the tools to query Splunk and build a complete picture of the incident."""

ENRICHMENT_PROMPT = """## Enrichment Phase

Enrich the investigation with threat intelligence and MITRE ATT&CK mapping.

Alert: {title}
Evidence collected:
{evidence_summary}

Tasks:
1. Check involved IPs and domains against threat intelligence.
2. Map observed attacker techniques to MITRE ATT&CK framework.
3. Identify all Indicators of Compromise (IOCs): IPs, domains, hashes, URLs.
4. Assess the risk level of each IOC (critical/high/medium/low).
5. Determine the geographic origin of the attack if possible.

Use the check_threat_intel tool for indicator lookups."""

VERDICT_PROMPT = """## Verdict Phase

You have completed the investigation of alert "{title}".

**Complete Evidence Package:**
{evidence_summary}

Now render your final verdict. You MUST call the `submit_verdict` tool with:
- **verdict**: "true_positive", "false_positive", or "escalate"
- **confidence**: a float between 0.0 and 1.0
- **summary**: a concise executive summary (2-3 paragraphs)
- **recommendations**: a JSON list of actionable recommendations

Decision framework:
- **True Positive**: Clear evidence of malicious activity; the alert is valid.
- **False Positive**: Evidence shows benign activity; the alert was triggered incorrectly.
- **Escalate**: Insufficient evidence or indicators suggest a sophisticated attack requiring human review.

Be decisive. Call submit_verdict now."""

REPORT_PROMPT = """Generate a comprehensive investigation report in JSON format with the following structure:

{{
    "summary": "Executive summary of the investigation (2-3 paragraphs)",
    "timeline": [
        {{"time": "ISO timestamp", "event": "Description of event", "source": "data source"}}
    ],
    "iocs": [
        {{"type": "ip|domain|hash|url|email", "value": "the indicator", "context": "why relevant", "risk_level": "critical|high|medium|low"}}
    ],
    "mitre_techniques": [
        {{"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"}}
    ],
    "recommendations": [
        "Specific actionable recommendation"
    ],
    "evidence": [
        {{"source": "data source", "description": "what was found", "data": {{}}}}
    ]
}}

Investigation context:
{evidence_summary}"""


# ═══════════════════════════════════════════════════════════════════════
#  TOOL DEFINITIONS  (OpenAI function-calling format)
# ═══════════════════════════════════════════════════════════════════════

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_splunk",
            "description": (
                "Execute an arbitrary SPL (Splunk Processing Language) query against the Splunk environment. "
                "Use this to search logs, correlate events, and gather evidence. "
                "Returns a list of matching events as JSON objects."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SPL query to execute, e.g. 'index=botsv1 src_ip=\"203.0.113.50\" | stats count by sourcetype'",
                    },
                    "earliest": {
                        "type": "string",
                        "description": "Earliest time for the search window, e.g. '-24h', '-7d', '2026-06-11T00:00:00'. Default: '-24h'",
                        "default": "-24h",
                    },
                    "latest": {
                        "type": "string",
                        "description": "Latest time for the search window, e.g. 'now', '2026-06-12T00:00:00'. Default: 'now'",
                        "default": "now",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_activity",
            "description": (
                "Retrieve a summary of all activity for a specific user across all data sources. "
                "Returns event counts by sourcetype and action."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "The username to investigate, e.g. 'admin', 'jsmith'",
                    },
                },
                "required": ["username"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ip_activity",
            "description": (
                "Retrieve a summary of all activity for a specific IP address. "
                "Returns event counts by sourcetype, unique destinations, and byte counts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ip_address": {
                        "type": "string",
                        "description": "The IP address to investigate, e.g. '203.0.113.50'",
                    },
                },
                "required": ["ip_address"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_event_timeline",
            "description": (
                "Get a chronological timeline of events for an entity (IP or user). "
                "Useful for understanding the sequence of attacker actions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "entity": {
                        "type": "string",
                        "description": "The entity value (IP address or username)",
                    },
                    "entity_type": {
                        "type": "string",
                        "enum": ["ip", "user"],
                        "description": "Whether the entity is an IP address or username",
                    },
                    "timerange": {
                        "type": "string",
                        "description": "Time range to search, e.g. '-1h', '-24h', '-7d'. Default: '-24h'",
                        "default": "-24h",
                    },
                },
                "required": ["entity", "entity_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_threat_intel",
            "description": (
                "Check an indicator (IP, domain, hash, URL) against threat intelligence feeds. "
                "Returns reputation score, associated malware families, and historical reports."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "indicator": {
                        "type": "string",
                        "description": "The indicator to check, e.g. '203.0.113.50', 'evil.example.com'",
                    },
                    "indicator_type": {
                        "type": "string",
                        "enum": ["ip", "domain", "hash", "url"],
                        "description": "Type of the indicator",
                    },
                },
                "required": ["indicator", "indicator_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_verdict",
            "description": (
                "Submit the final investigation verdict. MUST be called exactly once at the end of the investigation. "
                "This concludes the investigation and generates the final report."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "verdict": {
                        "type": "string",
                        "enum": ["true_positive", "false_positive", "escalate"],
                        "description": "The final verdict for the alert",
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence level from 0.0 to 1.0",
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                    "summary": {
                        "type": "string",
                        "description": "Executive summary of the investigation (2-3 paragraphs)",
                    },
                    "recommendations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of actionable recommendations",
                    },
                },
                "required": ["verdict", "confidence", "summary", "recommendations"],
            },
        },
    },
]
