"""Trace mémoire légère du pipeline décisionnel de JARVIS."""

from dataclasses import dataclass
import logging
import os
from typing import Any, Optional


@dataclass
class DiagnosticEvent:
    stage: str
    source: Optional[str] = None
    success: Optional[bool] = None
    confidence: Optional[float] = None
    message: Optional[str] = None
    metadata: Optional[dict] = None


_last_diagnostics = []
_logger = logging.getLogger("jarvis.diagnostics")


def create_diagnostic_event(stage, source=None, success=None, confidence=None,
                            message=None, metadata=None):
    return DiagnosticEvent(stage, source, success, confidence, message, metadata)


def format_diagnostic(event):
    parts = [f"[{event.stage}]"]
    if event.source is not None:
        parts.append(f"source={event.source}")
    if event.confidence is not None:
        parts.append(f"confidence={event.confidence:.2f}")
    if event.success is not None:
        parts.append(f"success={event.success}")
    if event.message:
        parts.append(f"message={event.message}")
    metadata = event.metadata or {}
    for key in ("error_type", "fallback_allowed"):
        if key in metadata:
            parts.append(f"{key}={metadata[key]}")
    return " ".join(parts)


def record_diagnostic(event):
    _last_diagnostics.append(event)
    if os.getenv("JARVIS_DEBUG", "0").lower() in {"1", "true", "yes", "on"}:
        _logger.info(format_diagnostic(event))


def get_last_diagnostics():
    return list(_last_diagnostics)


def clear_diagnostics():
    _last_diagnostics.clear()
