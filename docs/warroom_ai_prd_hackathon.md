# Product Requirements Document: WarRoom (Hackathon Edition)

**Tagline:** Splunk AI Agent to investigate incidents from Slack

## 1. Problem Statement
* **Data Disconnect:** Security incidents are coordinated in Slack, but the forensic data lives in Splunk.
* **Context Switching:** Analysts waste critical response time toggling between chat applications and the Splunk Enterprise interface.
* **The Google Doc Nightmare:** Instead of hunting threats, the Incident Commander is stuck manually copy-pasting raw logs and IPs from Splunk into a frantic Google Doc—leading to fragmented timelines and agonizing post-incident reporting.

## 2. Solution Overview
WarRoom is an AI agent embedded in Slack. Powered by the **Splunk Model Context Protocol (MCP)** and **Splunk Hosted Models**, it fetches raw SIEM data, translates natural language into SPL, and continuously builds the incident timeline inside the chat.

## 3. Core Features

### 1. Plain-English to Splunk
Engineers stop writing complex Splunk queries under pressure.
* *Action:* An engineer asks `@WarRoom how many failed logins for user jsmith?`. The agent connects via Splunk MCP, translates the intent, runs the query, and replies in the thread with the exact logs.

### 2. The Scribe (Auto-Timeline)
The AI sits in the incident channel and "listens" to the human engineers.
* *Action:* It automatically extracts key findings (IPs, file hashes) and continuously updates a **Pinned Slack Message** with the master timeline. Late-joiners read the pinned message and are instantly caught up.

### 3. The Shift Handover
Major breaches span multiple days. Passing the torch between engineers is messy.
* *Action:* An engineer tags `@WarRoom generate shift handover for @Sarah`. The bot summarizes the last 8 hours of chat, lists the open tasks, and tags the incoming engineer so they are instantly up to speed.

### 4. 1-Click Post-Incident Report
When the threat is contained, the paperwork is already done.
* *Action:* An engineer tags `@WarRoom generate final report`. The bot takes its timeline and instantly exports a formatted Markdown report ready for executive review.

## 4. Hackathon Competitive Edge (The "Why We Win")
* **100% Splunk Native Stack:** WarRoom fully utilizes the Splunk AI ecosystem, proving that Splunk can act as the definitive backend engine for ChatOps.
* **Privacy by Design:** By exclusively using Splunk Hosted Models for LLM generation, we demonstrate how highly classified SOC chat logs never have to leave the Splunk secure perimeter.
