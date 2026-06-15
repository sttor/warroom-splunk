"""
WarRoom Investigation Models
============================
Pydantic models representing the full investigation lifecycle:
steps, IOCs, MITRE ATT&CK mappings, reports, and the top-level Investigation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from models.alerts import Alert


class InvestigationStep(BaseModel):
    """A single phase in the investigation pipeline."""

    name: Literal["triage", "context_gathering", "correlation", "enrichment", "verdict"] = Field(
        ..., description="Pipeline phase name"
    )
    status: Literal["pending", "running", "complete", "error"] = Field(
        default="pending", description="Current status of this step"
    )
    summary: Optional[str] = Field(default=None, description="Short human-readable summary")
    details: Optional[str] = Field(default=None, description="Extended analysis details (may include markdown)")
    data: Optional[dict[str, Any]] = Field(default=None, description="Raw data returned by Splunk queries")
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)


class IOC(BaseModel):
    """Indicator of Compromise extracted during investigation."""

    type: Literal["ip", "domain", "hash", "url", "email"] = Field(..., description="IOC category")
    value: str = Field(..., description="The indicator value")
    context: str = Field(..., description="Why this IOC is relevant to the investigation")
    risk_level: Literal["critical", "high", "medium", "low"] = Field(..., description="Assessed risk")


class IdentifiedAsset(BaseModel):
    """An asset identified as being involved in the incident."""

    name: str = Field(..., description="Asset identifier, e.g., vpn-gw-primary or 10.0.0.5")
    type: str = Field(..., description="Asset type, e.g., Endpoint, Server, User, Database")
    context: str = Field(..., description="How the asset is involved")


class ThreatClassification(BaseModel):
    """AI classification of the threat."""

    category: str = Field(..., description="High-level category, e.g., Brute Force, Malware, Data Exfil")
    confidence: float = Field(..., description="Confidence in this classification (0.0-1.0)")


class MitreTechnique(BaseModel):
    """A MITRE ATT&CK technique identified during investigation."""

    id: str = Field(..., description="Technique ID, e.g. T1110")
    name: str = Field(..., description="Technique name, e.g. Brute Force")
    tactic: str = Field(..., description="Parent tactic, e.g. Credential Access")


class InvestigationReport(BaseModel):
    """Final structured report produced at the end of an investigation."""

    summary: str = Field(..., description="Executive summary of the investigation")
    timeline: list[dict[str, Any]] = Field(default_factory=list, description="Chronological events")
    iocs: list[IOC] = Field(default_factory=list, description="Extracted IOCs")
    assets: list[IdentifiedAsset] = Field(default_factory=list, description="Identified assets involved")
    threat_classifications: list[ThreatClassification] = Field(default_factory=list, description="AI threat classifications")
    mitre_techniques: list[MitreTechnique] = Field(default_factory=list, description="Mapped MITRE techniques")
    recommendations: list[str] = Field(default_factory=list, description="Actionable recommendations")
    evidence: list[dict[str, Any]] = Field(default_factory=list, description="Key evidence artefacts")


class Investigation(BaseModel):
    """Top-level investigation object tying an alert to the analysis pipeline."""

    id: str = Field(..., description="Unique investigation ID")
    alert_id: str = Field(..., description="ID of the originating alert")
    alert: Alert = Field(..., description="Snapshot of the alert being investigated")
    status: Literal[
        "triage",
        "context_gathering",
        "correlation",
        "enrichment",
        "verdict",
        "complete",
        "error",
    ] = Field(default="triage", description="Current pipeline phase")
    verdict: Optional[Literal["true_positive", "false_positive", "escalate"]] = Field(
        default=None, description="Final verdict"
    )
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Confidence in the verdict (0-1)"
    )
    steps: list[InvestigationStep] = Field(default_factory=list, description="Ordered investigation steps")
    report: Optional[InvestigationReport] = Field(default=None, description="Final investigation report")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
