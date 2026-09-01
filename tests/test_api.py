"""
Pytest tests for the FloatChat FastAPI endpoints.

Runs without a live database or Ollama — the WorkflowEngine is mocked
so tests stay fast and hermetic.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Return a TestClient with WorkflowEngine fully mocked."""
    with patch("agentic_workflow.api.get_engine") as mock_factory:
        engine = MagicMock()
        engine.process_query.return_value = {
            "main_response": "Test response",
            "data_summary": {"profiles": 10},
            "visualizations": [],
            "recommendations": ["Check salinity"],
        }
        mock_factory.return_value = engine

        from agentic_workflow.api import app
        yield TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_status_field(self, client):
        data = client.get("/health").json()
        assert data["status"] == "ok"

    def test_version_field(self, client):
        data = client.get("/health").json()
        assert "version" in data

    def test_services_field(self, client):
        data = client.get("/health").json()
        assert isinstance(data["services"], dict)


# ---------------------------------------------------------------------------
# /stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_returns_200(self, client):
        assert client.get("/stats").status_code == 200

    def test_total_profiles(self, client):
        data = client.get("/stats").json()
        assert data["total_profiles"] == 4922

    def test_regions_present(self, client):
        data = client.get("/stats").json()
        assert "regions" in data

    def test_date_range(self, client):
        data = client.get("/stats").json()
        assert "start" in data["date_range"]
        assert "end" in data["date_range"]


# ---------------------------------------------------------------------------
# /regions
# ---------------------------------------------------------------------------

class TestRegions:
    def test_returns_200(self, client):
        assert client.get("/regions").status_code == 200

    def test_has_regions_key(self, client):
        data = client.get("/regions").json()
        assert "regions" in data


# ---------------------------------------------------------------------------
# /anomalies
# ---------------------------------------------------------------------------

class TestAnomalies:
    def test_returns_200(self, client):
        assert client.get("/anomalies").status_code == 200

    def test_response_shape(self, client):
        data = client.get("/anomalies").json()
        assert "count" in data
        assert "contamination_rate" in data
        assert isinstance(data["anomalies"], list)

    def test_limit_param(self, client):
        data = client.get("/anomalies?limit=2").json()
        assert data["count"] <= 2

    def test_region_filter(self, client):
        data = client.get("/anomalies?region=Arabian").json()
        for anomaly in data["anomalies"]:
            assert "Arabian" in anomaly["region"]


# ---------------------------------------------------------------------------
# /jobs (async queue)
# ---------------------------------------------------------------------------

class TestJobs:
    def test_submit_returns_202(self, client):
        r = client.post("/jobs", json={"query": "What is the thermocline depth?"})
        assert r.status_code == 202

    def test_submit_returns_job_id(self, client):
        r = client.post("/jobs", json={"query": "Test"})
        assert "job_id" in r.json()

    def test_get_job_not_found(self, client):
        r = client.get("/jobs/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404

    def test_get_existing_job(self, client):
        job_id = client.post("/jobs", json={"query": "Test"}).json()["job_id"]
        r = client.get(f"/jobs/{job_id}")
        assert r.status_code == 200
        assert r.json()["job_id"] == job_id


# ---------------------------------------------------------------------------
# /sessions history
# ---------------------------------------------------------------------------

class TestSessionHistory:
    def test_empty_history(self, client):
        r = client.get("/sessions/nonexistent-session/history")
        assert r.status_code == 200
        assert r.json()["count"] == 0

    def test_clear_history(self, client):
        r = client.delete("/sessions/nonexistent-session/history")
        assert r.status_code == 200
        assert "deleted" in r.json()
