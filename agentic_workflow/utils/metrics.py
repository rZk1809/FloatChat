"""Optional Prometheus metrics for the FloatChat FastAPI server.

Metrics are collected only when the *prometheus_client* package is installed.
If it is absent, all functions become no-ops so the rest of the codebase
does not need to guard every call site.

Usage:
    from agentic_workflow.utils.metrics import (
        record_query_duration, record_query_intent, inc_error_counter
    )
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

    _QUERY_DURATION = Histogram(
        "floatchat_query_duration_seconds",
        "End-to-end /query endpoint latency in seconds",
        buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60],
        labelnames=["region"],
    )

    _QUERY_COUNTER = Counter(
        "floatchat_queries_total",
        "Total number of /query requests",
        labelnames=["intent", "status"],
    )

    _ACTIVE_JOBS = Gauge(
        "floatchat_active_jobs",
        "Number of async jobs currently running",
    )

    _ERROR_COUNTER = Counter(
        "floatchat_errors_total",
        "Total number of errors raised in the workflow",
        labelnames=["component"],
    )

    _PROMETHEUS_AVAILABLE = True

except ImportError:  # pragma: no cover
    _PROMETHEUS_AVAILABLE = False
    generate_latest = None  # type: ignore[assignment]
    CONTENT_TYPE_LATEST = "text/plain"


def record_query_duration(seconds: float, region: str = "unknown") -> None:
    if _PROMETHEUS_AVAILABLE:
        _QUERY_DURATION.labels(region=region).observe(seconds)


def record_query(intent: str = "unknown", status: str = "ok") -> None:
    if _PROMETHEUS_AVAILABLE:
        _QUERY_COUNTER.labels(intent=intent, status=status).inc()


def set_active_jobs(count: int) -> None:
    if _PROMETHEUS_AVAILABLE:
        _ACTIVE_JOBS.set(count)


def inc_error_counter(component: str = "unknown") -> None:
    if _PROMETHEUS_AVAILABLE:
        _ERROR_COUNTER.labels(component=component).inc()


def get_metrics_response() -> tuple[bytes | str, str]:
    """Return (body, content_type) for a Prometheus scrape endpoint."""
    if _PROMETHEUS_AVAILABLE and generate_latest is not None:
        return generate_latest(), CONTENT_TYPE_LATEST
    return b"# prometheus_client not installed\n", "text/plain"


def prometheus_available() -> bool:
    return _PROMETHEUS_AVAILABLE
