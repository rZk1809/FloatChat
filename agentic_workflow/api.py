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

from .core.config import config
from .core.workflow_engine import WorkflowEngine

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


@app.get("/regions", tags=["Data"])
async def list_regions():
    """Return the geographic regions supported by FloatChat."""
    return {"regions": config.system.regions}


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

    return QueryResponse(
        session_id=session_id,
        query=req.query,
        main_response=result.get("main_response", ""),
        data_summary=result.get("data_summary", {}),
        visualizations=result.get("visualizations", []),
        recommendations=result.get("recommendations", []),
        processing_time_ms=elapsed_ms,
    )
