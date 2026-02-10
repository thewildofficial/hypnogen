"""Smoke tests for the FastAPI render worker.

Verifies:
- /health returns 200
- POST /v1/render-jobs submits and returns job_id
- GET /v1/render-jobs/{job_id} returns status
- GET /v1/render-jobs/{job_id}/artifacts returns artifact metadata
- DELETE /v1/render-jobs/{job_id} cancels a job
- Validation errors return proper HTTP codes
- Unknown job_id returns 404
- Artifacts for incomplete job returns 409
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class _NoOpRunner:
    """Stub runner that accepts jobs but never executes them.

    Used in tests to avoid importing heavy TTS dependencies and to keep
    job state deterministic (always stays PENDING unless explicitly changed).
    """

    def submit(self, job_id: str) -> None:
        pass

    def shutdown(self, wait: bool = True) -> None:
        pass


@pytest.fixture()
def client():
    """Create a test client with a fresh job store and no-op runner."""
    from hypnogen.api.app import create_app
    from hypnogen.api.worker import JobStore

    store = JobStore()
    runner = _NoOpRunner()
    app = create_app(job_store=store, job_runner=runner)
    return TestClient(app)


@pytest.fixture()
def sample_submit_body():
    """Minimal valid render job submission body."""
    return {
        "script": "Welcome to deep relaxation.",
        "affirmations": ["I am calm", "I am peaceful"],
    }


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """GET /health returns service status."""

    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Submit
# ---------------------------------------------------------------------------


class TestSubmitEndpoint:
    """POST /v1/render-jobs submits a render job."""

    def test_submit_returns_202(self, client, sample_submit_body):
        resp = client.post("/v1/render-jobs", json=sample_submit_body)
        assert resp.status_code == 202

    def test_submit_returns_job_id(self, client, sample_submit_body):
        resp = client.post("/v1/render-jobs", json=sample_submit_body)
        data = resp.json()
        assert "job_id" in data
        assert isinstance(data["job_id"], str)
        assert len(data["job_id"]) > 0

    def test_submit_returns_pending_status(self, client, sample_submit_body):
        resp = client.post("/v1/render-jobs", json=sample_submit_body)
        data = resp.json()
        assert data["status"] == "pending"
        assert data["progress"] == 0.0

    def test_submit_rejects_empty_script(self, client):
        body = {"script": "", "affirmations": ["I am calm"]}
        resp = client.post("/v1/render-jobs", json=body)
        assert resp.status_code == 422

    def test_submit_rejects_missing_affirmations(self, client):
        body = {"script": "Hello."}
        resp = client.post("/v1/render-jobs", json=body)
        assert resp.status_code == 422

    def test_submit_rejects_empty_affirmations(self, client):
        body = {"script": "Hello.", "affirmations": []}
        resp = client.post("/v1/render-jobs", json=body)
        assert resp.status_code == 422

    def test_submit_accepts_all_optional_fields(self, client):
        body = {
            "script": "Welcome.",
            "affirmations": ["I am calm"],
            "voice": "af_heart",
            "swarm_voice": "am_adam",
            "seed": 42,
            "length_sec": 600,
            "export_stems": True,
            "gain_db": {"swarm": -24.0},
        }
        resp = client.post("/v1/render-jobs", json=body)
        assert resp.status_code == 202


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


class TestStatusEndpoint:
    """GET /v1/render-jobs/{job_id} returns job status."""

    def test_status_returns_pending_after_submit(self, client, sample_submit_body):
        submit_resp = client.post("/v1/render-jobs", json=sample_submit_body)
        job_id = submit_resp.json()["job_id"]

        resp = client.get(f"/v1/render-jobs/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == job_id
        assert data["status"] in ("pending", "running", "completed", "failed")
        assert 0.0 <= data["progress"] <= 1.0

    def test_status_unknown_job_returns_404(self, client):
        resp = client.get("/v1/render-jobs/nonexistent-id")
        assert resp.status_code == 404

    def test_status_fields_match_schema(self, client, sample_submit_body):
        submit_resp = client.post("/v1/render-jobs", json=sample_submit_body)
        job_id = submit_resp.json()["job_id"]

        resp = client.get(f"/v1/render-jobs/{job_id}")
        data = resp.json()
        expected_keys = {"job_id", "status", "stage", "progress", "eta_sec", "error"}
        assert expected_keys == set(data.keys())


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------


class TestArtifactsEndpoint:
    """GET /v1/render-jobs/{job_id}/artifacts returns artifact metadata."""

    def test_artifacts_unknown_job_returns_404(self, client):
        resp = client.get("/v1/render-jobs/nonexistent-id/artifacts")
        assert resp.status_code == 404

    def test_artifacts_pending_job_returns_409(self, client, sample_submit_body):
        """Artifacts not available until job completes."""
        submit_resp = client.post("/v1/render-jobs", json=sample_submit_body)
        job_id = submit_resp.json()["job_id"]

        resp = client.get(f"/v1/render-jobs/{job_id}/artifacts")
        # Should be 409 Conflict — artifacts not yet available
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------


class TestCancelEndpoint:
    """DELETE /v1/render-jobs/{job_id} cancels a job."""

    def test_cancel_unknown_job_returns_404(self, client):
        resp = client.delete("/v1/render-jobs/nonexistent-id")
        assert resp.status_code == 404

    def test_cancel_pending_job_returns_200(self, client, sample_submit_body):
        submit_resp = client.post("/v1/render-jobs", json=sample_submit_body)
        job_id = submit_resp.json()["job_id"]

        resp = client.delete(f"/v1/render-jobs/{job_id}")
        assert resp.status_code == 200

    def test_cancelled_job_shows_failed_status(self, client, sample_submit_body):
        submit_resp = client.post("/v1/render-jobs", json=sample_submit_body)
        job_id = submit_resp.json()["job_id"]

        client.delete(f"/v1/render-jobs/{job_id}")
        resp = client.get(f"/v1/render-jobs/{job_id}")
        data = resp.json()
        assert data["status"] == "failed"
        assert "cancel" in data["error"].lower()


# ---------------------------------------------------------------------------
# Worker unit tests
# ---------------------------------------------------------------------------


class TestJobStore:
    """In-memory job store tracks jobs correctly."""

    def test_create_job(self):
        from hypnogen.api.models import RenderJobSubmit
        from hypnogen.api.worker import JobStore

        store = JobStore()
        submit = RenderJobSubmit(
            script="Hello.", affirmations=["I am calm"]
        )
        job_id = store.create_job(submit)
        assert isinstance(job_id, str)
        assert len(job_id) > 0

    def test_get_status(self):
        from hypnogen.api.models import JobStatus, RenderJobSubmit
        from hypnogen.api.worker import JobStore

        store = JobStore()
        submit = RenderJobSubmit(
            script="Hello.", affirmations=["I am calm"]
        )
        job_id = store.create_job(submit)
        status = store.get_status(job_id)
        assert status is not None
        assert status.job_id == job_id
        assert status.status == JobStatus.PENDING

    def test_get_status_unknown_returns_none(self):
        from hypnogen.api.worker import JobStore

        store = JobStore()
        assert store.get_status("nonexistent") is None

    def test_update_progress(self):
        from hypnogen.api.models import JobStatus, RenderJobSubmit
        from hypnogen.api.worker import JobStore

        store = JobStore()
        submit = RenderJobSubmit(
            script="Hello.", affirmations=["I am calm"]
        )
        job_id = store.create_job(submit)
        store.update_progress(job_id, 0.5, "Shepherd TTS: 5/10 segments")
        status = store.get_status(job_id)
        assert status.progress == 0.5
        assert status.stage == "Shepherd TTS: 5/10 segments"
        assert status.status == JobStatus.RUNNING

    def test_mark_completed(self):
        from hypnogen.api.models import JobStatus, RenderJobSubmit
        from hypnogen.api.worker import JobStore

        store = JobStore()
        submit = RenderJobSubmit(
            script="Hello.", affirmations=["I am calm"]
        )
        job_id = store.create_job(submit)
        result = {"paths": {"mix": "/tmp/mix.wav", "stems": {}, "metadata": "/tmp/render.json"}}
        store.mark_completed(job_id, result)
        status = store.get_status(job_id)
        assert status.status == JobStatus.COMPLETED
        assert status.progress == 1.0

    def test_mark_failed(self):
        from hypnogen.api.models import JobStatus, RenderJobSubmit
        from hypnogen.api.worker import JobStore

        store = JobStore()
        submit = RenderJobSubmit(
            script="Hello.", affirmations=["I am calm"]
        )
        job_id = store.create_job(submit)
        store.mark_failed(job_id, "Something went wrong")
        status = store.get_status(job_id)
        assert status.status == JobStatus.FAILED
        assert status.error == "Something went wrong"

    def test_cancel_sets_flag(self):
        from hypnogen.api.models import RenderJobSubmit
        from hypnogen.api.worker import JobStore

        store = JobStore()
        submit = RenderJobSubmit(
            script="Hello.", affirmations=["I am calm"]
        )
        job_id = store.create_job(submit)
        store.cancel(job_id)
        assert store.is_cancelled(job_id) is True

    def test_is_cancelled_false_by_default(self):
        from hypnogen.api.models import RenderJobSubmit
        from hypnogen.api.worker import JobStore

        store = JobStore()
        submit = RenderJobSubmit(
            script="Hello.", affirmations=["I am calm"]
        )
        job_id = store.create_job(submit)
        assert store.is_cancelled(job_id) is False
