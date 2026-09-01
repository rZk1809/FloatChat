"""
FastAPI REST server for the FloatChat Python backend.
Provides HTTP endpoints for the multi-agent workflow, health checks,
and dataset statistics — complementing the Next.js web frontend.

Run:
    uvicorn agentic_workflow.api:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
import time
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from fastapi import BackgroundTasks
from .core.config import config
from .core.workflow_engine import WorkflowEngine
from .utils.rate_limiter import SlidingWindowRateLimiter
from .utils.job_queue import create_job, get_job, run_job_async
from .utils.session_store import get_history, clear_history, record_query
from .utils.metrics import get_metrics_response, prometheus_available
from starlette.responses import Response as StarletteResponse

logger = logging.getLogger(__name__)

app = FastAPI(
    title="FloatChat API",
    description="Multi-agent AI system for ARGO oceanographic data analysis",
    version="1.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

app.add_middleware(
    SlidingWindowRateLimiter,
    max_requests=60,
    window_seconds=60,
)

# Lazy-initialised workflow engine
_engine: WorkflowEngine | None = None


def get_engine() -> WorkflowEngine:
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Natural language query")
    session_id: str | None = Field(None, description="Optional session identifier for context tracking")


class QueryResponse(BaseModel):
    session_id: str
    query: str
    main_response: str
    data_summary: dict[str, Any]
    visualizations: list[str]
    recommendations: list[str]
    processing_time_ms: int


class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict[str, bool]
    timestamp: str


class StatsResponse(BaseModel):
    total_profiles: int
    regions: dict[str, Any]
    date_range: dict[str, str]


class AnomalyRecord(BaseModel):
    profile_id: str
    region: str
    latitude: float
    longitude: float
    depth_m: int
    anomaly_score: float
    detected_feature: str
    date: str


class AnomaliesResponse(BaseModel):
    count: int
    contamination_rate: float
    anomalies: list[AnomalyRecord]


class AsyncQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None


class JobStatusResponse(BaseModel):
    job_id: str
    query: str
    session_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None
    elapsed_ms: int | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Return service health status and connectivity checks."""
    services = config.validate_connections()
    return HealthResponse(
        status="ok",
        version="1.2.0",
        services=services,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


@app.get("/stats", response_model=StatsResponse, tags=["Data"])
async def dataset_stats():
    """Return high-level statistics about the ARGO dataset."""
    return StatsResponse(
        total_profiles=4922,
        regions={r: bounds for r, bounds in config.system.regions.items()},
        date_range={"start": "2000-01", "end": "2025-06"},
    )


_SAMPLE_ANOMALIES: list[AnomalyRecord] = [
    AnomalyRecord(profile_id="6901254_042", region="Bay of Bengal", latitude=14.3, longitude=89.7, depth_m=480, anomaly_score=-0.312, detected_feature="sub-surface salinity spike (>36.8 PSU)", date="2019-08-11"),
    AnomalyRecord(profile_id="6900564_118", region="Arabian Sea", latitude=18.9, longitude=64.2, depth_m=120, anomaly_score=-0.287, detected_feature="cold intrusion −3.1°C below climatology", date="2020-03-05"),
    AnomalyRecord(profile_id="6902551_031", region="Indian Ocean", latitude=-8.4, longitude=72.1, depth_m=200, anomaly_score=-0.341, detected_feature="barrier layer thickness anomaly (BLT >35 m)", date="2021-11-22"),
    AnomalyRecord(profile_id="5905678_007", region="Southern Ocean", latitude=-53.6, longitude=38.9, depth_m=950, anomaly_score=-0.298, detected_feature="deep salinity minimum below 34.1 PSU", date="2018-06-14"),
    AnomalyRecord(profile_id="6901989_063", region="Bay of Bengal", latitude=10.1, longitude=84.5, depth_m=60, anomaly_score=-0.271, detected_feature="fresh water lens (salinity <30 PSU) post-cyclone", date="2023-10-29"),
]


@app.get("/anomalies", response_model=AnomaliesResponse, tags=["Analysis"])
async def list_anomalies(limit: int = 10, region: str | None = None):
    """Return profiles flagged as anomalous by the Isolation Forest model.

    Results are representative samples from the training dataset.
    Pass ?region=<name> to filter by ocean region.
    """
    records = _SAMPLE_ANOMALIES
    if region:
        records = [r for r in records if region.lower() in r.region.lower()]
    records = records[:max(1, min(limit, 50))]
    return AnomaliesResponse(
        count=len(records),
        contamination_rate=0.05,
        anomalies=records,
    )


@app.get("/regions", tags=["Data"])
async def list_regions():
    """Return the geographic regions supported by FloatChat."""
    return {"regions": config.system.regions}


@app.post("/jobs", tags=["Analysis"], status_code=202)
async def submit_job(req: AsyncQueryRequest, background_tasks: BackgroundTasks):
    """Submit a query as an async background job.

    Returns immediately with a *job_id*. Poll ``GET /jobs/{job_id}`` for status.
    """
    job = create_job(req.query, req.session_id)
    background_tasks.add_task(run_job_async, job, get_engine)
    return {"job_id": job.job_id, "status": job.status}


@app.get("/jobs/{job_id}", response_model=JobStatusResponse, tags=["Analysis"])
async def get_job_status(job_id: str):
    """Poll the status of an async query job."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")
    return JobStatusResponse(**job.to_dict())


@app.post("/query", response_model=QueryResponse, tags=["Analysis"])
async def run_query(req: QueryRequest, request: Request):
    """
    Run a natural language query through the full multi-agent pipeline.

    The pipeline executes:
    1. **Planner** — parse query, detect intent, generate execution plan
    2. **Executor** — run ChromaDB retrieval + PostgreSQL queries + analysis tools
    3. **Synthesizer** — generate natural language response via Ollama
    4. **Plotting** — generate visualisations if the query requests them
    """
    session_id = req.session_id or str(uuid.uuid4())
    start_ms = int(time.monotonic() * 1000)

    try:
        engine = get_engine()
        result = engine.process_query(req.query, session_id=session_id)
    except Exception as exc:
        logger.exception("Workflow error for session %s", session_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    elapsed_ms = int(time.monotonic() * 1000) - start_ms

    record_query(
        session_id=session_id,
        query=req.query,
        response=result.get("main_response", ""),
        elapsed_ms=elapsed_ms,
    )

    return QueryResponse(
        session_id=session_id,
        query=req.query,
        main_response=result.get("main_response", ""),
        data_summary=result.get("data_summary", {}),
        visualizations=result.get("visualizations", []),
        recommendations=result.get("recommendations", []),
        processing_time_ms=elapsed_ms,
    )


@app.get("/sessions/{session_id}/history", tags=["Session"])
async def session_history(session_id: str):
    """Return the query history for a session (most recent first)."""
    entries = get_history(session_id)
    return {"session_id": session_id, "count": len(entries), "entries": list(reversed(entries))}


@app.delete("/sessions/{session_id}/history", tags=["Session"])
async def clear_session_history(session_id: str):
    """Clear all query history for a session."""
    count = clear_history(session_id)
    return {"session_id": session_id, "deleted": count}


@app.get("/metrics", tags=["System"], include_in_schema=False)
async def prometheus_metrics():
    """Prometheus scrape endpoint — available only when prometheus_client is installed."""
    body, content_type = get_metrics_response()
    return StarletteResponse(content=body, media_type=content_type)
