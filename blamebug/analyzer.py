"""LLM chain: classify severity and produce structured remediation."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from openai import OpenAI

from blamebug.models import IncidentAnalysis, Severity

SYSTEM_PROMPT = """You are FaultLine, an SRE assistant. You receive raw backend logs, stack traces, or error snippets.

Rules:
- Infer severity from symptoms: data loss/outage → critical; user-facing errors or failed payments → high; degraded performance or retries → medium; noisy logs or warnings → low; purely informational → info.
- If logs are ambiguous, choose a conservative severity and lower confidence.
- immediate_actions must be ordered, verifiable steps (shell, dashboard checks, rollbacks) when possible.
- long_term_remediation must include monitoring/alerting and code or infra changes where relevant.
- Respond ONLY with valid JSON matching the schema described in the user message. No markdown fences."""

USER_SCHEMA_HINT = """Return a JSON object with exactly these keys:
- severity: one of "critical","high","medium","low","info"
- title: string
- summary: string
- root_cause_hypothesis: string
- impact_assessment: string
- affected_components: array of strings
- immediate_actions: array of strings (at least 1)
- long_term_remediation: array of strings (at least 1)
- confidence: number between 0 and 1"""

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
# Default Groq chat model (fast, strong JSON following). Override with FAULTLINE_LLM_MODEL.
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def _api_key() -> str:
    return (os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY", "")).strip()


def _base_url() -> Optional[str]:
    explicit = os.environ.get("OPENAI_BASE_URL", "").strip()
    if explicit:
        return explicit
    if os.environ.get("GROQ_API_KEY", "").strip():
        return GROQ_BASE_URL
    return None


def _default_model() -> str:
    override = os.environ.get("FAULTLINE_LLM_MODEL", "").strip() or os.environ.get(
        "BLAMEBUG_LLM_MODEL", ""
    ).strip()
    if override:
        return override
    if os.environ.get("GROQ_API_KEY", "").strip():
        return DEFAULT_GROQ_MODEL
    return DEFAULT_OPENAI_MODEL


def _client() -> OpenAI:
    return OpenAI(api_key=_api_key() or "dummy", base_url=_base_url())


def analyze_logs(
    raw_logs: str,
    *,
    model: Optional[str] = None,
    extra_context: Optional[str] = None,
) -> IncidentAnalysis:
    """Run the LLM chain and validate structured output."""
    m = model or _default_model()
    client = _client()

    user_parts: list[str] = [USER_SCHEMA_HINT, "", "--- LOGS ---", raw_logs.strip()]
    if extra_context:
        user_parts.extend(["", "--- CONTEXT ---", extra_context])

    completion = client.chat.completions.create(
        model=m,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "\n".join(user_parts)},
        ],
    )

    text = completion.choices[0].message.content or "{}"
    data: dict[str, Any] = json.loads(text)

    # Normalize severity string to enum
    sev_raw = str(data.get("severity", "medium")).lower()
    try:
        data["severity"] = Severity(sev_raw)
    except ValueError:
        data["severity"] = Severity.MEDIUM

    return IncidentAnalysis.model_validate(data)


def is_configured() -> bool:
    return bool(_api_key())
