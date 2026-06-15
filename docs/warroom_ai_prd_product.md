# Product Requirements Document: WarRoom (Commercial Product Edition)

**Tagline:** AI Agent to investigate incidents from Slack

## 1. Problem Statement
* **Data Disconnect:** Security incidents are coordinated in Slack, but the forensic data lives in siloed platforms (SIEMs, EDRs, Threat Feeds).
* **Context Switching:** Analysts waste critical response time toggling between chat applications and security dashboards.
* **The Google Doc Nightmare:** Instead of hunting threats, the Incident Commander is stuck manually copy-pasting raw logs and IPs from multiple dashboards into a frantic Google Doc—leading to fragmented timelines and agonizing post-incident reporting.

## 2. Solution Overview
WarRoom is an autonomous AI agent embedded directly in Slack incident channels. Managed via a simple Admin Dashboard, it connects instantly to your existing security stack (Splunk, Elastic, CrowdStrike). WarRoom acts as an active technical teammate—fetching raw SIEM data, translating natural language into complex queries, and continuously building the definitive incident timeline entirely inside the chat.

## 3. Core Features

### 1. SIEM-Agnostic Querying
Engineers stop writing complex queries under pressure.
* *Action:* An engineer asks `@WarRoom how many failed logins for user jsmith?`. The agent translates the intent, runs the query across Splunk/Elastic, and replies in the thread with the exact logs.

### 2. The Scribe (Auto-Timeline)
The AI sits in the incident channel and "listens" to the human engineers.
* *Action:* It automatically extracts key findings (IPs, file hashes) and continuously updates a **Pinned Slack Message** with the master timeline. Late-joiners read the pinned message and are instantly caught up.

### 3. The Shift Handover
Major breaches span multiple days. Passing the torch between engineers is messy.
* *Action:* An engineer tags `@WarRoom generate shift handover for @Sarah`. The bot summarizes the last 8 hours of chat, lists the open tasks, and tags the incoming engineer so they are instantly up to speed.

### 4. 1-Click Post-Incident Report
When the threat is contained, the paperwork is already done.
* *Action:* An engineer tags `@WarRoom generate final report`. The bot takes its timeline and instantly exports a formatted PDF/Markdown report ready for executive review.

### 5. Zero-Click Auto-Enrichment
When an engineer drops an unknown IP address or domain into the chat, the bot acts as a junior analyst.
* *Action:* It automatically (without being tagged) checks external threat feeds (VirusTotal, GreyNoise) and replies in the thread with the reputation score.

## 4. Competitive Moat
Current ChatOps tools (like Incident.io or Rootly) manage the *human workflow* (paging, ticketing). WarRoom manages the *data workflow*. It is the only platform that acts as the "Data Intelligence Layer," plugging into existing Incident.io channels to bring the full analytical power of the SOC directly into the chat interface.

## 5. Enterprise Readiness (Procurement Requirements)
* **Bring Your Own Model (BYOM):** Support for Local LLMs (Ollama) or Private Cloud Tenants (Azure OpenAI) to guarantee zero data retention by public AI providers.
* **Role-Based Access Control (RBAC):** WarRoom inherits the exact SIEM permissions of the human Slack user requesting the data.
