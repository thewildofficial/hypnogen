"""Local job runner with in-memory state for the Render API.

Manages render jobs: creation, progress tracking, completion, failure,
and cancellation. Runs render_session() in a background thread so the
FastAPI event loop is never blocked.

The JobStore is the single source of truth for job state. It is
designed for local single-process use (dict-backed); a future SaaS
deployment would swap this for a database-backed store.
"""

from __future__ import annotations

import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

from hypnogen.api.models import (
    JobStatus,
    RenderJobArtifacts,
    RenderJobStatus,
    RenderJobSubmit,
)

DEFAULT_JOBS_DIR = os.path.join(".sisyphus", "jobs")
MAX_WORKERS = 1  # Serial execution — keeps model warm in one thread


class JobStore:
    """Thread-safe in-memory store for render job state.

    Each job has:
    - status (RenderJobStatus): current lifecycle state
    - request (RenderJobSubmit): original submission
    - result (dict | None): render_session() return value on completion
    - cancelled (bool): cancellation flag checked by progress callback
    """

    def __init__(self, jobs_dir: str = DEFAULT_JOBS_DIR) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self.jobs_dir = jobs_dir

    def create_job(self, request: RenderJobSubmit) -> str:
        """Create a new pending job and return its ID."""
        job_id = uuid.uuid4().hex
        status = RenderJobStatus(
            job_id=job_id,
            status=JobStatus.PENDING,
            progress=0.0,
        )
        with self._lock:
            self._jobs[job_id] = {
                "status": status,
                "request": request,
                "result": None,
                "cancelled": False,
            }
        return job_id

    def get_status(self, job_id: str) -> RenderJobStatus | None:
        """Return current status or None if job_id unknown."""
        with self._lock:
            entry = self._jobs.get(job_id)
            return entry["status"] if entry else None

    def get_request(self, job_id: str) -> RenderJobSubmit | None:
        """Return original submit request or None."""
        with self._lock:
            entry = self._jobs.get(job_id)
            return entry["request"] if entry else None

    def get_result(self, job_id: str) -> dict[str, Any] | None:
        """Return render result dict or None."""
        with self._lock:
            entry = self._jobs.get(job_id)
            return entry["result"] if entry else None

    def update_progress(
        self, job_id: str, progress: float, stage: str
    ) -> None:
        """Update progress fraction and stage description.

        Automatically transitions to RUNNING on first progress update.
        """
        with self._lock:
            entry = self._jobs.get(job_id)
            if entry is None:
                return
            old = entry["status"]
            entry["status"] = RenderJobStatus(
                job_id=job_id,
                status=JobStatus.RUNNING,
                stage=stage,
                progress=progress,
                eta_sec=old.eta_sec,
                error=None,
            )

    def mark_completed(self, job_id: str, result: dict[str, Any]) -> None:
        """Transition job to COMPLETED with render result."""
        with self._lock:
            entry = self._jobs.get(job_id)
            if entry is None:
                return
            entry["result"] = result
            entry["status"] = RenderJobStatus(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                progress=1.0,
            )

    def mark_failed(self, job_id: str, error: str) -> None:
        """Transition job to FAILED with error message."""
        with self._lock:
            entry = self._jobs.get(job_id)
            if entry is None:
                return
            old = entry["status"]
            entry["status"] = RenderJobStatus(
                job_id=job_id,
                status=JobStatus.FAILED,
                progress=old.progress,
                error=error,
            )

    def cancel(self, job_id: str) -> bool:
        """Set cancellation flag. Returns True if job existed."""
        with self._lock:
            entry = self._jobs.get(job_id)
            if entry is None:
                return False
            entry["cancelled"] = True
            old = entry["status"]
            entry["status"] = RenderJobStatus(
                job_id=job_id,
                status=JobStatus.FAILED,
                progress=old.progress,
                error="Cancelled by user",
            )
            return True

    def is_cancelled(self, job_id: str) -> bool:
        """Check whether cancellation was requested."""
        with self._lock:
            entry = self._jobs.get(job_id)
            if entry is None:
                return False
            return entry["cancelled"]

    def has_job(self, job_id: str) -> bool:
        """Check if a job_id exists."""
        with self._lock:
            return job_id in self._jobs

    def get_artifacts(self, job_id: str) -> RenderJobArtifacts | None:
        """Build artifact metadata from the completed result.

        Returns None if job is not completed.
        """
        with self._lock:
            entry = self._jobs.get(job_id)
            if entry is None:
                return None
            if entry["status"].status != JobStatus.COMPLETED:
                return None
            result = entry["result"]
            if result is None:
                return None

        paths = result.get("paths", {})
        return RenderJobArtifacts(
            job_id=job_id,
            mix_wav_url=paths.get("mix", ""),
            stems=paths.get("stems", {}),
            metadata_url=paths.get("metadata", ""),
            created_at=datetime.now(tz=timezone.utc),
        )


class JobRunner:
    """Executes render jobs in a background thread pool.

    Keeps the TTS model warm by reusing a single worker thread
    (MAX_WORKERS=1). Jobs are queued and executed serially.
    """

    def __init__(self, store: JobStore) -> None:
        self._store = store
        self._executor = ThreadPoolExecutor(
            max_workers=MAX_WORKERS, thread_name_prefix="render"
        )

    def submit(self, job_id: str) -> None:
        """Queue a job for background execution.

        Retrieves the request from the store and runs render_session()
        in a background thread.
        """
        request = self._store.get_request(job_id)
        if request is None:
            return
        self._executor.submit(self._run, job_id, request)

    def _run(self, job_id: str, request: RenderJobSubmit) -> None:
        """Execute render_session() and update the store."""
        from hypnogen.core.render import render_session

        output_dir = os.path.join(self._store.jobs_dir, job_id)
        os.makedirs(output_dir, exist_ok=True)

        def progress_callback(fraction: float, description: str) -> None:
            if self._store.is_cancelled(job_id):
                raise _CancelledError(job_id)
            self._store.update_progress(job_id, fraction, description)

        try:
            result = render_session(
                script_text=request.script,
                affirmations=request.affirmations,
                output_dir=output_dir,
                voice=request.voice,
                swarm_voice=request.swarm_voice,
                seed=request.seed,
                length_sec=request.length_sec,
                export_stems=request.export_stems,
                gain_db=request.gain_db,
                progress_callback=progress_callback,
            )
            self._store.mark_completed(job_id, result)
        except _CancelledError:
            # Already marked as failed/cancelled by store.cancel()
            pass
        except Exception as exc:
            self._store.mark_failed(job_id, str(exc))

    def shutdown(self, wait: bool = True) -> None:
        """Shut down the thread pool."""
        self._executor.shutdown(wait=wait)


class _CancelledError(Exception):
    """Raised inside render_session when cancellation is detected."""

    def __init__(self, job_id: str) -> None:
        super().__init__(f"Job {job_id} cancelled")
        self.job_id = job_id
