"""Simple in-memory async job queue for long-running workflow queries.

Jobs are stored in a module-level dict and executed as FastAPI background
tasks. This is intentionally lightweight — suitable for single-process
development and demo deployments. For production, replace with Celery +
Redis or a similar durable queue.
"""

import asyncio
import logging
import time
import uuid
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class JobRecord:
    def __init__(self, job_id: str, query: str, session_id: str) -> None:
        self.job_id = job_id
        self.query = query
        self.session_id = session_id
        self.status: JobStatus = JobStatus.PENDING
        self.result: dict[str, Any] | None = None
        self.error: str | None = None
        self.created_at: float = time.monotonic()
        self.started_at: float | None = None
        self.finished_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        elapsed = None
        if self.started_at and self.finished_at:
            elapsed = int((self.finished_at - self.started_at) * 1000)
        return {
            "job_id": self.job_id,
            "query": self.query,
            "session_id": self.session_id,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "elapsed_ms": elapsed,
        }


_jobs: dict[str, JobRecord] = {}
_MAX_JOBS = 500
_JOB_TTL_S = 3600


def _evict_old_jobs() -> None:
    now = time.monotonic()
    stale = [jid for jid, j in _jobs.items() if now - j.created_at > _JOB_TTL_S]
    for jid in stale:
        del _jobs[jid]
    if len(_jobs) > _MAX_JOBS:
        oldest = sorted(_jobs.keys(), key=lambda k: _jobs[k].created_at)
        for jid in oldest[: len(_jobs) - _MAX_JOBS]:
            del _jobs[jid]


def create_job(query: str, session_id: str | None = None) -> JobRecord:
    _evict_old_jobs()
    job_id = str(uuid.uuid4())
    sid = session_id or str(uuid.uuid4())
    job = JobRecord(job_id=job_id, query=query, session_id=sid)
    _jobs[job_id] = job
    return job


def get_job(job_id: str) -> JobRecord | None:
    return _jobs.get(job_id)


async def run_job_async(job: JobRecord, engine_factory) -> None:
    job.status = JobStatus.RUNNING
    job.started_at = time.monotonic()
    try:
        engine = engine_factory()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: engine.process_query(job.query, session_id=job.session_id)
        )
        job.result = result
        job.status = JobStatus.DONE
    except Exception as exc:
        logger.exception("Job %s failed", job.job_id)
        job.error = str(exc)
        job.status = JobStatus.FAILED
    finally:
        job.finished_at = time.monotonic()
