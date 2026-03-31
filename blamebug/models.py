from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IncidentAnalysis(BaseModel):
    """Structured LLM output for an incident report."""

    severity: Severity = Field(description="Impact and urgency of the incident")
    title: str = Field(max_length=200, description="Short headline for the incident")
    summary: str = Field(description="2–4 sentence executive summary")
    root_cause_hypothesis: str = Field(
        description="Best-effort hypothesis from logs; state uncertainty if unclear"
    )
    impact_assessment: str = Field(
        description="User/system impact in plain language"
    )
    affected_components: List[str] = Field(
        default_factory=list,
        description="Services, jobs, DBs, queues, etc. mentioned or implied",
    )
    immediate_actions: List[str] = Field(
        min_length=1,
        description="Concrete steps to stop bleeding or verify state now",
    )
    long_term_remediation: List[str] = Field(
        min_length=1,
        description="Hardening, tests, alerts, refactors to prevent recurrence",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="0–1 confidence in this analysis given log quality",
    )


class WebhookPayload(BaseModel):
    """Incoming webhook body from n8n or other automation."""

    logs: str = Field(min_length=1, description="Raw error or stack trace text")
    source: Optional[str] = None
    metadata: Optional[dict] = None
