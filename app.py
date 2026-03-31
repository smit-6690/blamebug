"""
Entry point for `uvicorn app:app` (local + Hugging Face Spaces).
"""

import os

# Disable Gradio telemetry by default (no outbound analytics on import).
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from blamebug.server import app  # noqa: E402

__all__ = ["app"]
