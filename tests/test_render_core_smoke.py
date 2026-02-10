"""Smoke tests for the render-core entry point.

Verifies that render_session() orchestrates the full pipeline:
parse → shepherd TTS → swarm TTS → bed → mix → export.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest


MOCK_TTS_SR = 24000
MOCK_AUDIO = np.zeros(MOCK_TTS_SR, dtype=np.float32)  # 1 second of silence


@pytest.fixture
def mock_tts():
    """Mock TTS and effects to avoid model download and heavy DSP."""
    with patch("hypnogen.core.render.synthesize") as mock_synth, \
         patch("hypnogen.core.effects.apply_pitch_shift", side_effect=lambda a, sr, n: a.copy()), \
         patch("hypnogen.core.effects.apply_time_stretch", side_effect=lambda a, r: a.copy()):
        mock_synth.return_value = (MOCK_AUDIO, MOCK_TTS_SR)
        yield mock_synth


class TestRenderSessionAPI:
    """Test that render_session has the expected API surface."""

    def test_render_session_is_importable(self):
        """render_session can be imported from hypnogen.core.render."""
        from hypnogen.core.render import render_session

        assert callable(render_session)

    def test_render_session_accepts_required_params(self, mock_tts):
        """render_session accepts script_text, affirmations, and output_dir."""
        from hypnogen.core.render import render_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text="Welcome to relaxation.",
                affirmations=["I am calm", "I am peaceful"],
                output_dir=tmpdir,
            )
            assert result is not None

    def test_render_session_accepts_config_params(self, mock_tts):
        """render_session accepts optional config parameters."""
        from hypnogen.core.render import render_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text="Welcome.",
                affirmations=["I am calm"],
                output_dir=tmpdir,
                voice="af_heart",
                seed=42,
                length_sec=10,
                sr=44100,
            )
            assert result is not None


class TestRenderSessionOutput:
    """Test that render_session produces the expected output structure."""

    def test_returns_dict_with_paths_key(self, mock_tts):
        """render_session returns a dict containing 'paths'."""
        from hypnogen.core.render import render_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text="Welcome.",
                affirmations=["I am calm"],
                output_dir=tmpdir,
            )
            assert isinstance(result, dict)
            assert "paths" in result

    def test_returns_dict_with_metadata_key(self, mock_tts):
        """render_session returns a dict containing 'metadata'."""
        from hypnogen.core.render import render_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text="Welcome.",
                affirmations=["I am calm"],
                output_dir=tmpdir,
            )
            assert "metadata" in result
            assert isinstance(result["metadata"], dict)

    def test_paths_contains_mix_wav(self, mock_tts):
        """Paths dict includes 'mix' pointing to a WAV file."""
        from hypnogen.core.render import render_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text="Welcome.",
                affirmations=["I am calm"],
                output_dir=tmpdir,
            )
            assert "mix" in result["paths"]
            mix_path = result["paths"]["mix"]
            assert mix_path.endswith(".wav")
            assert Path(mix_path).exists()

    def test_creates_render_json(self, mock_tts):
        """render_session writes render.json metadata file."""
        from hypnogen.core.render import render_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text="Welcome.",
                affirmations=["I am calm"],
                output_dir=tmpdir,
            )
            render_json = Path(tmpdir) / "render.json"
            assert render_json.exists()

            with open(render_json) as f:
                data = json.load(f)
            assert "sample_rate" in data
            assert "duration_sec" in data

    def test_creates_stems_when_requested(self, mock_tts):
        """render_session creates stem WAV files when export_stems=True."""
        from hypnogen.core.render import render_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text="Welcome.",
                affirmations=["I am calm"],
                output_dir=tmpdir,
                export_stems=True,
            )
            assert "stems" in result["paths"]
            stems = result["paths"]["stems"]
            assert isinstance(stems, dict)
            # Should have shepherd, swarm, bed stem files
            assert "shepherd" in stems
            assert "swarm" in stems
            assert "bed" in stems
            for stem_path in stems.values():
                assert Path(stem_path).exists()

    def test_skips_stems_by_default(self, mock_tts):
        """render_session does NOT create stems by default."""
        from hypnogen.core.render import render_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text="Welcome.",
                affirmations=["I am calm"],
                output_dir=tmpdir,
            )
            # stems key may be absent or empty
            stems = result["paths"].get("stems", {})
            assert stems == {} or stems is None or len(stems) == 0


class TestRenderSessionBehavior:
    """Test pipeline behavior through render_session."""

    def test_processes_embedded_commands(self, mock_tts):
        """render_session handles scripts with <cmd> tags."""
        from hypnogen.core.render import render_session

        script = 'You can <cmd pitch="-2">relax deeply</cmd> now.'
        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text=script,
                affirmations=["I am calm"],
                output_dir=tmpdir,
            )
            assert Path(result["paths"]["mix"]).exists()

    def test_processes_pause_tags(self, mock_tts):
        """render_session handles scripts with <pause> tags."""
        from hypnogen.core.render import render_session

        script = 'Welcome.\n<pause duration="500ms"/>\nRelax.'
        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text=script,
                affirmations=["I am calm"],
                output_dir=tmpdir,
            )
            assert Path(result["paths"]["mix"]).exists()

    def test_seed_produces_deterministic_output(self, mock_tts):
        """Same seed produces identical metadata."""
        from hypnogen.core.render import render_session

        results = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as tmpdir:
                result = render_session(
                    script_text="Welcome.",
                    affirmations=["I am calm"],
                    output_dir=tmpdir,
                    seed=42,
                )
                results.append(result["metadata"])

        assert results[0]["seed"] == results[1]["seed"]
        assert results[0]["duration_sec"] == results[1]["duration_sec"]

    def test_metadata_contains_expected_fields(self, mock_tts):
        """Metadata includes seed, duration_sec, sample_rate, voices."""
        from hypnogen.core.render import render_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text="Welcome.",
                affirmations=["I am calm"],
                output_dir=tmpdir,
                seed=42,
                voice="af_heart",
            )
            meta = result["metadata"]
            assert "seed" in meta
            assert "duration_sec" in meta
            assert "sample_rate" in meta
            assert "voices" in meta

    def test_respects_custom_length_sec(self, mock_tts):
        """render_session uses provided length_sec."""
        from hypnogen.core.render import render_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text="Welcome.",
                affirmations=["I am calm"],
                output_dir=tmpdir,
                length_sec=15,
            )
            assert result["metadata"]["duration_sec"] == 15

    def test_separate_shepherd_swarm_voices(self, mock_tts):
        """render_session supports separate shepherd and swarm voices."""
        from hypnogen.core.render import render_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text="Welcome.",
                affirmations=["I am calm"],
                output_dir=tmpdir,
                voice="af_heart",
                swarm_voice="am_adam",
            )
            voices = result["metadata"]["voices"]
            assert voices["shepherd"] == "af_heart"
            assert voices["swarm"] == "am_adam"

    def test_default_voice_used_for_both(self, mock_tts):
        """When only voice is given, it's used for both shepherd and swarm."""
        from hypnogen.core.render import render_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text="Welcome.",
                affirmations=["I am calm"],
                output_dir=tmpdir,
                voice="af_heart",
            )
            voices = result["metadata"]["voices"]
            assert voices["shepherd"] == "af_heart"
            assert voices["swarm"] == "af_heart"


class TestRenderSessionProgress:
    """Test optional progress callback support."""

    def test_accepts_progress_callback(self, mock_tts):
        """render_session accepts optional progress_callback."""
        from hypnogen.core.render import render_session

        calls = []

        def on_progress(fraction: float, description: str):
            calls.append((fraction, description))

        with tempfile.TemporaryDirectory() as tmpdir:
            render_session(
                script_text="Welcome.",
                affirmations=["I am calm"],
                output_dir=tmpdir,
                progress_callback=on_progress,
            )

        assert len(calls) > 0
        # First call should be 0.0, last should be 1.0
        assert calls[0][0] == 0.0
        assert calls[-1][0] == 1.0

    def test_works_without_progress_callback(self, mock_tts):
        """render_session works fine when no progress_callback is given."""
        from hypnogen.core.render import render_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text="Welcome.",
                affirmations=["I am calm"],
                output_dir=tmpdir,
            )
            assert Path(result["paths"]["mix"]).exists()


class TestRenderSessionGainDB:
    """Test custom gain dB support for subliminal level control."""

    def test_accepts_gain_db_override(self, mock_tts):
        """render_session accepts gain_db dict for per-layer gain."""
        from hypnogen.core.render import render_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_session(
                script_text="Welcome.",
                affirmations=["I am calm"],
                output_dir=tmpdir,
                gain_db={"swarm": -24.0},
            )
            assert Path(result["paths"]["mix"]).exists()
