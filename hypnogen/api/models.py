"""Pydantic models for the Render Job HTTP API contract.

Defines the stable, JSON-serializable request/response types shared by all
clients (CLI, Gradio, SwiftUI macOS app, future web SaaS).

Models:
    RenderJobSubmit   - POST /v1/render-jobs request body
    RenderJobStatus   - GET  /v1/render-jobs/{job_id} response
    RenderJobArtifacts - GET  /v1/render-jobs/{job_id}/artifacts response
    JobStatus         - Enum of job lifecycle states
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Constants (mirrored from render-core defaults for single source of truth)
# ---------------------------------------------------------------------------

DEFAULT_VOICE = "af_heart"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class JobStatus(str, Enum):
    """Lifecycle states of a render job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class RenderJobSubmit(BaseModel):
    """Submit a new render job.

    Maps 1-to-1 with the parameters of ``render_session()`` in
    ``hypnogen.core.render``.  Fields use the same names and defaults so the
    FastAPI worker can forward them without translation.
    """

    script: str = Field(
        ...,
        min_length=1,
        description="Raw hypnotic script text with optional XML-style tags.",
    )
    affirmations: list[str] = Field(
        ...,
        min_length=1,
        description="List of affirmation strings for the subliminal swarm.",
    )
    voice: str = Field(
        default=DEFAULT_VOICE,
        description="TTS voice for shepherd (main narration) track.",
    )
    swarm_voice: Optional[str] = Field(
        default=None,
        description="TTS voice for swarm track. Defaults to same as voice.",
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility. None = random.",
    )
    length_sec: Optional[int] = Field(
        default=None,
        gt=0,
        description="Session length in seconds. None = derived from script.",
    )
    export_stems: bool = Field(
        default=False,
        description="Whether to export individual stem WAV files.",
    )
    gain_db: Optional[dict[str, float]] = Field(
        default=None,
        description='Per-layer gain overrides in dB, e.g. {"swarm": -24.0}.',
    )

    @field_validator("script")
    @classmethod
    def script_not_blank(cls, v: str) -> str:
        """Reject whitespace-only scripts."""
        if not v.strip():
            raise ValueError("Script must contain non-whitespace content.")
        return v


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class RenderJobStatus(BaseModel):
    """Current status of a render job.

    Returned by the status-polling endpoint. Clients use ``progress`` and
    ``stage`` to render a progress bar and ETA.
    """

    job_id: str = Field(
        ...,
        description="Unique identifier for the render job.",
    )
    status: JobStatus = Field(
        ...,
        description="Current lifecycle state of the job.",
    )
    stage: Optional[str] = Field(
        default=None,
        description='Human-readable stage description, e.g. "Shepherd TTS: 3/10 segments".',
    )
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Fractional progress (0.0 to 1.0).",
    )
    eta_sec: Optional[int] = Field(
        default=None,
        description="Estimated seconds remaining. None when unknown.",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message when status is FAILED.",
    )


class RenderJobArtifacts(BaseModel):
    """Artifact metadata for a completed render job.

    Paths/URLs point to the mix WAV, optional stems, and the render metadata
    JSON.  In local mode these are filesystem paths; in SaaS mode they become
    pre-signed URLs.
    """

    job_id: str = Field(
        ...,
        description="Unique identifier for the render job.",
    )
    mix_wav_url: str = Field(
        ...,
        description="Path or URL to the final mixed WAV file.",
    )
    stems: dict[str, str] = Field(
        default_factory=dict,
        description='Mapping of stem name to path/URL, e.g. {"shepherd": "/path/shepherd.wav"}.',
    )
    metadata_url: str = Field(
        ...,
        description="Path or URL to the render.json metadata file.",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when artifacts were created (ISO 8601).",
    )
