"""In-memory report store (replace with Redis/DB in production)."""

from __future__ import annotations

from collections import OrderedDict
from threading import Lock
from typing import List, Optional, Tuple

MAX_REPORTS = 100


class ReportStore:
    def __init__(self) -> None:
        self._lock = Lock()
        # id -> (severity, html_for_api, text_for_ui)
        self._by_id: OrderedDict[str, Tuple[str, str, str]] = OrderedDict()

    def save(self, report_id: str, severity: str, html: str, text: str) -> None:
        with self._lock:
            self._by_id[report_id] = (severity, html, text)
            self._by_id.move_to_end(report_id)
            while len(self._by_id) > MAX_REPORTS:
                self._by_id.popitem(last=False)

    def get(self, report_id: str) -> Optional[str]:
        with self._lock:
            t = self._by_id.get(report_id)
            return t[1] if t else None

    def latest(self) -> Optional[Tuple[str, str, str]]:
        """(report_id, html, text)"""
        with self._lock:
            if not self._by_id:
                return None
            rid, (_, html, text) = next(reversed(self._by_id.items()))
            return rid, html, text

    def list_recent(self, limit: int = 20) -> List[Tuple[str, str]]:
        with self._lock:
            out: List[Tuple[str, str]] = []
            for rid, (sev, _, _) in reversed(list(self._by_id.items())):
                out.append((rid, sev))
                if len(out) >= limit:
                    break
            return out


store = ReportStore()
