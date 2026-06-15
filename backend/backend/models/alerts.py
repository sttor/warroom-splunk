"""
WarRoom Alert Models
===================
Pydantic data models representing security alerts ingested from Splunk.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class Alert(BaseModel):
    """A single security alert / notable event from Splunk."""

    id: str = Field(..., description="Unique alert identifier")
    title: str = Field(..., description="Human-readable alert title")
    severity: Literal["critical", "high", "medium", "low", "info"] = Field(
        ..., description="Alert severity level"
    )
    source_ip: Optional[str] = Field(default=None, description="Source IP address")
    dest_ip: Optional[str] = Field(default=None, description="Destination IP address")
    user: Optional[str] = Field(default=None, description="Associated username")
    timestamp: datetime = Field(..., description="When the alert was generated")
    description: str = Field(..., description="Detailed alert description")
    status: Literal["new", "investigating", "resolved"] = Field(
        default="new", description="Current triage status"
    )
    attack_type: str = Field(
        ...,
        description="Category of attack, e.g. brute_force, lateral_movement, data_exfiltration",
    )
    raw_event: Optional[dict[str, Any]] = Field(
        default=None, description="Raw event data from Splunk"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "ALERT-001",
                "title": "Multiple Failed SSH Logins",
                "severity": "high",
                "source_ip": "203.0.113.50",
                "dest_ip": "192.0.2.10",
                "user": "admin",
                "timestamp": "2026-06-12T10:30:00Z",
                "description": "52 failed SSH login attempts detected from 203.0.113.50 targeting admin account.",
                "status": "new",
                "attack_type": "brute_force",
            }
        }
