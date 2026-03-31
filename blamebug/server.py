"""FastAPI app: webhook + Gradio UI."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import time
import uuid
from typing import Optional

import gradio as gr
from fastapi import APIRouter, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from blamebug.analyzer import analyze_logs, is_configured
from blamebug.models import WebhookPayload
from blamebug.report_html import build_report_html, build_report_text, gradio_html_iframe
from blamebug.store import store


def _expected_webhook_secret() -> Optional[str]:
    # Prefer renamed env var, keep old one for backward compatibility.
    s = os.environ.get("FAULTLINE_WEBHOOK_SECRET", "").strip() or os.environ.get(
        "BLAMEBUG_WEBHOOK_SECRET", ""
    ).strip()
    return s or None


def _run_pipeline(
    raw_logs: str,
    *,
    source: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> tuple[str, str, str, float, str]:
    """Returns (report_id, html_ui_for_gradio, html_stored, seconds, severity)."""
    t0 = time.perf_counter()
    analysis = analyze_logs(raw_logs)
    rid = str(uuid.uuid4())
    sev = analysis.severity.value
    html_full = build_report_html(
        analysis,
        raw_logs,
        report_id=rid,
        source=source,
        metadata=metadata,
    )
    text_ui = build_report_text(
        analysis,
        raw_logs,
        report_id=rid,
        source=source,
        metadata=metadata,
    )
    html_ui = gradio_html_iframe(html_full)
    store.save(rid, sev, html_full, text_ui)
    elapsed = time.perf_counter() - t0
    return rid, html_ui, html_full, elapsed, sev


def create_app() -> FastAPI:
    app = FastAPI(title="FaultLine", version="0.1.0")
    api = APIRouter(prefix="/api")

    class WebhookResponse(BaseModel):
        report_id: str
        severity: str
        processing_seconds: float
        ok: bool = True

    @api.get("/reports/{report_id}", response_class=HTMLResponse)
    def get_report(report_id: str) -> HTMLResponse:
        html_doc = store.get(report_id)
        if not html_doc:
            raise HTTPException(status_code=404, detail="Report not found")
        return HTMLResponse(content=html_doc)

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "llm_configured": is_configured(),
        }

    @api.post("/webhook", response_model=WebhookResponse)
    def webhook(
        body: WebhookPayload,
        x_faultline_secret: Optional[str] = Header(None, alias="X-FaultLine-Secret"),
        x_blamebug_secret: Optional[str] = Header(None, alias="X-BlameBug-Secret"),
    ) -> WebhookResponse:
        secret = _expected_webhook_secret()
        provided_secret = x_faultline_secret or x_blamebug_secret
        if secret and provided_secret != secret:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
        if not is_configured():
            raise HTTPException(
                status_code=503,
                detail="GROQ_API_KEY or OPENAI_API_KEY not configured",
            )
        rid, _text, _html, elapsed, sev = _run_pipeline(
            body.logs,
            source=body.source,
            metadata=body.metadata,
        )
        return WebhookResponse(
            report_id=rid,
            severity=sev,
            processing_seconds=round(elapsed, 3),
        )

    app.include_router(api)

    def ui_analyze(logs: str, src: str) -> tuple[str, str]:
        if not logs or not logs.strip():
            return "", "Paste logs or trigger the webhook."
        if not is_configured():
            return (
                "",
                "Set GROQ_API_KEY (or OPENAI_API_KEY) in the environment (e.g. Space secrets or `.env`).",
            )
        try:
            meta = {"ui": True} if src else None
            rid, html_ui, _html, elapsed, sev = _run_pipeline(
                logs.strip(),
                source=src.strip() or None,
                metadata=meta,
            )
            status = f"Report `{rid}` · **{sev}** · {elapsed:.2f}s"
            return html_ui, status
        except Exception as e:
            return "", f"Error: {e!s}"

    def ui_refresh_latest() -> tuple[str, str]:
        latest = store.latest()
        if not latest:
            return "", "No reports yet."
        rid, html_full, _text = latest
        return gradio_html_iframe(html_full), f"Showing latest: `{rid}`"

    with gr.Blocks(
        title="FaultLine",
        theme=gr.themes.Soft(primary_hue="slate", neutral_hue="gray"),
    ) as demo:
        gr.Markdown(
            "# FaultLine\n"
            "Paste logs below and click **Analyze**."
        )
        with gr.Row():
            logs_in = gr.Textbox(
                label="Raw error logs / stack trace",
                placeholder="Paste stderr, JSON logs, or tracebacks…",
                lines=14,
            )
        src_in = gr.Textbox(
            label="Source (optional)",
            placeholder="e.g. prod-api / payment-worker",
        )
        with gr.Row():
            go = gr.Button("Analyze", variant="primary")
            refresh = gr.Button("Load latest report")
        status = gr.Markdown()
        report = gr.HTML(label="Incident report")

        go.click(ui_analyze, [logs_in, src_in], [report, status])
        refresh.click(ui_refresh_latest, [], [report, status])

    return gr.mount_gradio_app(app, demo, path="/")


app = create_app()
