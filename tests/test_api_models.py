"""Tests for the Render API Pydantic models.

Verifies:
- RenderJobSubmit validates submit requests
- RenderJobStatus validates status responses
- RenderJobArtifacts validates artifact metadata
- JSON serialization/deserialization round-trips
- Validation rejects invalid data
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Import tests
# ---------------------------------------------------------------------------


class TestModelsImportable:
    """All API models can be imported."""

    def test_render_job_submit_importable(self):
        from hypnogen.api.models import RenderJobSubmit

        assert RenderJobSubmit is not None

    def test_render_job_status_importable(self):
        from hypnogen.api.models import RenderJobStatus

        assert RenderJobStatus is not None

    def test_render_job_artifacts_importable(self):
        from hypnogen.api.models import RenderJobArtifacts

        assert RenderJobArtifacts is not None

    def test_job_status_enum_importable(self):
        from hypnogen.api.models import JobStatus

        assert JobStatus is not None


# ---------------------------------------------------------------------------
# RenderJobSubmit
# ---------------------------------------------------------------------------


class TestRenderJobSubmit:
    """RenderJobSubmit validates render submission requests."""

    def test_minimal_valid_submit(self):
        """Accepts script + affirmations (all else defaults)."""
        from hypnogen.api.models import RenderJobSubmit

        job = RenderJobSubmit(
            script="Welcome to relaxation.",
            affirmations=["I am calm", "I am peaceful"],
        )
        assert job.script == "Welcome to relaxation."
        assert job.affirmations == ["I am calm", "I am peaceful"]

    def test_full_valid_submit(self):
        """Accepts all fields explicitly."""
        from hypnogen.api.models import RenderJobSubmit

        job = RenderJobSubmit(
            script="Welcome.",
            affirmations=["I am calm"],
            voice="af_heart",
            swarm_voice="am_adam",
            seed=42,
            length_sec=600,
            export_stems=True,
            gain_db={"swarm": -24.0},
        )
        assert job.voice == "af_heart"
        assert job.swarm_voice == "am_adam"
        assert job.seed == 42
        assert job.length_sec == 600
        assert job.export_stems is True
        assert job.gain_db == {"swarm": -24.0}

    def test_defaults(self):
        """Default values match render-core defaults."""
        from hypnogen.api.models import RenderJobSubmit

        job = RenderJobSubmit(
            script="Welcome.",
            affirmations=["I am calm"],
        )
        assert job.voice == "af_heart"
        assert job.swarm_voice is None
        assert job.seed is None
        assert job.length_sec is None
        assert job.export_stems is False
        assert job.gain_db is None

    def test_rejects_empty_script(self):
        """Empty script is rejected."""
        from hypnogen.api.models import RenderJobSubmit

        with pytest.raises(ValidationError):
            RenderJobSubmit(script="", affirmations=["I am calm"])

    def test_rejects_whitespace_only_script(self):
        """Whitespace-only script is rejected."""
        from hypnogen.api.models import RenderJobSubmit

        with pytest.raises(ValidationError):
            RenderJobSubmit(script="   \n  ", affirmations=["I am calm"])

    def test_rejects_empty_affirmations_list(self):
        """At least one affirmation is required."""
        from hypnogen.api.models import RenderJobSubmit

        with pytest.raises(ValidationError):
            RenderJobSubmit(script="Welcome.", affirmations=[])

    def test_rejects_missing_script(self):
        """Script field is required."""
        from hypnogen.api.models import RenderJobSubmit

        with pytest.raises(ValidationError):
            RenderJobSubmit(affirmations=["I am calm"])

    def test_rejects_missing_affirmations(self):
        """Affirmations field is required."""
        from hypnogen.api.models import RenderJobSubmit

        with pytest.raises(ValidationError):
            RenderJobSubmit(script="Welcome.")

    def test_rejects_negative_length_sec(self):
        """length_sec must be positive."""
        from hypnogen.api.models import RenderJobSubmit

        with pytest.raises(ValidationError):
            RenderJobSubmit(
                script="Welcome.",
                affirmations=["I am calm"],
                length_sec=-10,
            )

    def test_rejects_zero_length_sec(self):
        """length_sec must be > 0."""
        from hypnogen.api.models import RenderJobSubmit

        with pytest.raises(ValidationError):
            RenderJobSubmit(
                script="Welcome.",
                affirmations=["I am calm"],
                length_sec=0,
            )

    def test_json_round_trip(self):
        """Serializes to JSON and deserializes back."""
        from hypnogen.api.models import RenderJobSubmit

        original = RenderJobSubmit(
            script="Welcome.",
            affirmations=["I am calm", "I am peaceful"],
            voice="af_heart",
            seed=42,
            length_sec=600,
        )
        json_str = original.model_dump_json()
        restored = RenderJobSubmit.model_validate_json(json_str)
        assert restored == original

    def test_dict_round_trip(self):
        """Serializes to dict and back."""
        from hypnogen.api.models import RenderJobSubmit

        original = RenderJobSubmit(
            script="Welcome.",
            affirmations=["I am calm"],
        )
        data = original.model_dump()
        restored = RenderJobSubmit.model_validate(data)
        assert restored == original


# ---------------------------------------------------------------------------
# RenderJobStatus
# ---------------------------------------------------------------------------


class TestRenderJobStatus:
    """RenderJobStatus validates job status responses."""

    def test_pending_status(self):
        """Can represent a pending job."""
        from hypnogen.api.models import JobStatus, RenderJobStatus

        status = RenderJobStatus(
            job_id="abc-123",
            status=JobStatus.PENDING,
        )
        assert status.job_id == "abc-123"
        assert status.status == JobStatus.PENDING
        assert status.stage is None
        assert status.progress == 0.0
        assert status.eta_sec is None
        assert status.error is None

    def test_running_status_with_progress(self):
        """Can represent a running job with progress info."""
        from hypnogen.api.models import JobStatus, RenderJobStatus

        status = RenderJobStatus(
            job_id="abc-123",
            status=JobStatus.RUNNING,
            stage="Shepherd TTS: 3/10 segments",
            progress=0.35,
            eta_sec=120,
        )
        assert status.status == JobStatus.RUNNING
        assert status.stage == "Shepherd TTS: 3/10 segments"
        assert status.progress == 0.35
        assert status.eta_sec == 120

    def test_completed_status(self):
        """Can represent a completed job."""
        from hypnogen.api.models import JobStatus, RenderJobStatus

        status = RenderJobStatus(
            job_id="abc-123",
            status=JobStatus.COMPLETED,
            progress=1.0,
        )
        assert status.status == JobStatus.COMPLETED
        assert status.progress == 1.0

    def test_failed_status_with_error(self):
        """Can represent a failed job with error message."""
        from hypnogen.api.models import JobStatus, RenderJobStatus

        status = RenderJobStatus(
            job_id="abc-123",
            status=JobStatus.FAILED,
            error="TTS model download failed",
        )
        assert status.status == JobStatus.FAILED
        assert status.error == "TTS model download failed"

    def test_rejects_missing_job_id(self):
        """job_id is required."""
        from hypnogen.api.models import JobStatus, RenderJobStatus

        with pytest.raises(ValidationError):
            RenderJobStatus(status=JobStatus.PENDING)

    def test_rejects_missing_status(self):
        """status is required."""
        from hypnogen.api.models import RenderJobStatus

        with pytest.raises(ValidationError):
            RenderJobStatus(job_id="abc-123")

    def test_rejects_invalid_status_string(self):
        """Only valid status enum values accepted."""
        from hypnogen.api.models import RenderJobStatus

        with pytest.raises(ValidationError):
            RenderJobStatus(job_id="abc-123", status="unknown")

    def test_rejects_progress_below_zero(self):
        """progress must be >= 0."""
        from hypnogen.api.models import JobStatus, RenderJobStatus

        with pytest.raises(ValidationError):
            RenderJobStatus(
                job_id="abc-123",
                status=JobStatus.RUNNING,
                progress=-0.1,
            )

    def test_rejects_progress_above_one(self):
        """progress must be <= 1."""
        from hypnogen.api.models import JobStatus, RenderJobStatus

        with pytest.raises(ValidationError):
            RenderJobStatus(
                job_id="abc-123",
                status=JobStatus.RUNNING,
                progress=1.5,
            )

    def test_json_round_trip(self):
        """Serializes to JSON and deserializes back."""
        from hypnogen.api.models import JobStatus, RenderJobStatus

        original = RenderJobStatus(
            job_id="abc-123",
            status=JobStatus.RUNNING,
            stage="Mixing layers",
            progress=0.8,
            eta_sec=30,
        )
        json_str = original.model_dump_json()
        restored = RenderJobStatus.model_validate_json(json_str)
        assert restored == original

    def test_status_enum_values(self):
        """JobStatus enum has expected values."""
        from hypnogen.api.models import JobStatus

        assert JobStatus.PENDING == "pending"
        assert JobStatus.RUNNING == "running"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.FAILED == "failed"


# ---------------------------------------------------------------------------
# RenderJobArtifacts
# ---------------------------------------------------------------------------


class TestRenderJobArtifacts:
    """RenderJobArtifacts validates artifact metadata."""

    def test_minimal_artifacts(self):
        """Can represent artifacts with just mix WAV."""
        from hypnogen.api.models import RenderJobArtifacts

        now = datetime.now(tz=timezone.utc)
        artifacts = RenderJobArtifacts(
            job_id="abc-123",
            mix_wav_url="/artifacts/abc-123/mix.wav",
            metadata_url="/artifacts/abc-123/render.json",
            created_at=now,
        )
        assert artifacts.job_id == "abc-123"
        assert artifacts.mix_wav_url == "/artifacts/abc-123/mix.wav"
        assert artifacts.metadata_url == "/artifacts/abc-123/render.json"
        assert artifacts.stems == {}
        assert artifacts.created_at == now

    def test_artifacts_with_stems(self):
        """Can include stem URLs."""
        from hypnogen.api.models import RenderJobArtifacts

        now = datetime.now(tz=timezone.utc)
        artifacts = RenderJobArtifacts(
            job_id="abc-123",
            mix_wav_url="/artifacts/abc-123/mix.wav",
            metadata_url="/artifacts/abc-123/render.json",
            stems={
                "shepherd": "/artifacts/abc-123/shepherd.wav",
                "swarm": "/artifacts/abc-123/swarm.wav",
                "bed": "/artifacts/abc-123/bed.wav",
            },
            created_at=now,
        )
        assert len(artifacts.stems) == 3
        assert "shepherd" in artifacts.stems

    def test_rejects_missing_job_id(self):
        """job_id is required."""
        from hypnogen.api.models import RenderJobArtifacts

        with pytest.raises(ValidationError):
            RenderJobArtifacts(
                mix_wav_url="/mix.wav",
                metadata_url="/render.json",
                created_at=datetime.now(tz=timezone.utc),
            )

    def test_rejects_missing_mix_wav_url(self):
        """mix_wav_url is required."""
        from hypnogen.api.models import RenderJobArtifacts

        with pytest.raises(ValidationError):
            RenderJobArtifacts(
                job_id="abc-123",
                metadata_url="/render.json",
                created_at=datetime.now(tz=timezone.utc),
            )

    def test_rejects_missing_metadata_url(self):
        """metadata_url is required."""
        from hypnogen.api.models import RenderJobArtifacts

        with pytest.raises(ValidationError):
            RenderJobArtifacts(
                job_id="abc-123",
                mix_wav_url="/mix.wav",
                created_at=datetime.now(tz=timezone.utc),
            )

    def test_rejects_missing_created_at(self):
        """created_at is required."""
        from hypnogen.api.models import RenderJobArtifacts

        with pytest.raises(ValidationError):
            RenderJobArtifacts(
                job_id="abc-123",
                mix_wav_url="/mix.wav",
                metadata_url="/render.json",
            )

    def test_json_round_trip(self):
        """Serializes to JSON and deserializes back."""
        from hypnogen.api.models import RenderJobArtifacts

        now = datetime.now(tz=timezone.utc)
        original = RenderJobArtifacts(
            job_id="abc-123",
            mix_wav_url="/mix.wav",
            metadata_url="/render.json",
            stems={"shepherd": "/shepherd.wav"},
            created_at=now,
        )
        json_str = original.model_dump_json()
        restored = RenderJobArtifacts.model_validate_json(json_str)
        assert restored == original

    def test_created_at_serializes_as_iso(self):
        """created_at serializes as ISO 8601 string in JSON."""
        from hypnogen.api.models import RenderJobArtifacts

        now = datetime(2026, 2, 11, 12, 0, 0, tzinfo=timezone.utc)
        artifacts = RenderJobArtifacts(
            job_id="abc-123",
            mix_wav_url="/mix.wav",
            metadata_url="/render.json",
            created_at=now,
        )
        json_str = artifacts.model_dump_json()
        assert "2026-02-11" in json_str
