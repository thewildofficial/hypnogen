"""FastAPI render worker — local-first, SaaS-ready.

Exposes the Render Job HTTP API:
    GET  /health                          → service health check
    POST /v1/render-jobs                  → submit render job (async)
    GET  /v1/render-jobs/{job_id}         → poll job status
    GET  /v1/render-jobs/{job_id}/artifacts → get artifact metadata
    DELETE /v1/render-jobs/{job_id}       → cancel job

Start locally::

    python -m hypnogen.api.app          # listens on 0.0.0.0:8008
    HYPNOGEN_PORT=9000 python -m hypnogen.api.app   # custom port
"""

from __future__ import annotations

import os
from typing import Protocol

from fastapi import FastAPI, HTTPException

from hypnogen.api.models import (
    RenderJobArtifacts,
    RenderJobStatus,
    RenderJobSubmit,
)
from hypnogen.api.worker import JobRunner, JobStore

DEFAULT_PORT = 8008
ENV_PORT_KEY = "HYPNOGEN_PORT"


class _RunnerLike(Protocol):
    """Minimal interface for a job runner (allows test stubs)."""

    def submit(self, job_id: str) -> None: ...
    def shutdown(self, wait: bool = True) -> None: ...


def create_app(
    *,
    job_store: JobStore | None = None,
    job_runner: _RunnerLike | None = None,
) -> FastAPI:
    """Build the FastAPI application.

    Accepts optional store/runner for dependency injection in tests.
    When omitted, creates defaults suitable for local operation.
    """
    store = job_store or JobStore()
    runner = job_runner or JobRunner(store)

    app = FastAPI(
        title="Hypnogen Render Worker",
        version="0.1.0",
        description="Local-first render API for hypnosis audio generation.",
    )

    # Store references on the app for shutdown hook
    app.state.store = store
    app.state.runner = runner

    # ------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Service health check."""
        return {"status": "ok"}

    @app.post(
        "/v1/render-jobs",
        status_code=202,
        response_model=RenderJobStatus,
    )
    async def submit_job(body: RenderJobSubmit) -> RenderJobStatus:
        """Submit a new render job.

        Returns immediately with job_id. The render executes in the
        background; poll GET /v1/render-jobs/{job_id} for progress.
        """
        job_id = store.create_job(body)
        runner.submit(job_id)
        status = store.get_status(job_id)
        return status  # type: ignore[return-value]

    @app.get(
        "/v1/render-jobs/{job_id}",
        response_model=RenderJobStatus,
    )
    async def get_job_status(job_id: str) -> RenderJobStatus:
        """Poll job status."""
        status = store.get_status(job_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return status

    @app.get(
        "/v1/render-jobs/{job_id}/artifacts",
        response_model=RenderJobArtifacts,
    )
    async def get_job_artifacts(job_id: str) -> RenderJobArtifacts:
        """Retrieve artifact metadata for a completed job."""
        if not store.has_job(job_id):
            raise HTTPException(status_code=404, detail="Job not found")
        artifacts = store.get_artifacts(job_id)
        if artifacts is None:
            raise HTTPException(
                status_code=409,
                detail="Artifacts not yet available (job not completed)",
            )
        return artifacts

    @app.delete("/v1/render-jobs/{job_id}")
    async def cancel_job(job_id: str) -> dict[str, str]:
        """Cancel a running or pending job."""
        if not store.has_job(job_id):
            raise HTTPException(status_code=404, detail="Job not found")
        store.cancel(job_id)
        return {"detail": "Job cancelled"}

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Clean up thread pool on shutdown."""
        runner.shutdown(wait=False)

    return app


# ------------------------------------------------------------------
# Entry point: python -m hypnogen.api.app
# ------------------------------------------------------------------

app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get(ENV_PORT_KEY, DEFAULT_PORT))
    uvicorn.run(
        "hypnogen.api.app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
