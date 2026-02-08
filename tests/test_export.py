"""Tests for export module (stems I/O + metadata JSON)."""

import json
import os
import tempfile

import numpy as np
import pytest
import soundfile as sf


class TestWriteWav:
    """Tests for write_wav function."""

    def test_creates_file_with_correct_shape(self):
        """write_wav creates WAV file with correct sample count."""
        from hypnogen.core.export import write_wav

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.wav")
            audio = np.zeros((44100, 2), dtype=np.float32)
            write_wav(filepath, audio, sr=44100)

            assert os.path.exists(filepath)
            data, sr = sf.read(filepath)
            assert data.shape == (44100, 2)
            assert sr == 44100

    def test_creates_mono_file(self):
        """write_wav handles mono audio correctly."""
        from hypnogen.core.export import write_wav

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "mono.wav")
            audio = np.zeros(22050, dtype=np.float32)
            write_wav(filepath, audio, sr=44100)

            data, sr = sf.read(filepath)
            assert data.shape == (22050,)
            assert sr == 44100

    def test_round_trip_samples_match(self):
        """Write WAV, read it back, verify samples match."""
        from hypnogen.core.export import write_wav

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "roundtrip.wav")
            rng = np.random.default_rng(42)
            audio = rng.uniform(-1.0, 1.0, (44100, 2)).astype(np.float32)
            
            write_wav(filepath, audio, sr=44100)
            data, sr = sf.read(filepath)

            np.testing.assert_array_almost_equal(audio, data, decimal=6)

    def test_uses_float_subtype(self):
        """write_wav uses 32-bit float WAV format."""
        from hypnogen.core.export import write_wav

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "float.wav")
            audio = np.array([[0.5, -0.5], [0.25, -0.25]], dtype=np.float32)
            write_wav(filepath, audio, sr=44100)

            info = sf.info(filepath)
            assert info.subtype == "FLOAT"


class TestExportStems:
    """Tests for export_stems function."""

    def test_creates_all_expected_files(self):
        """export_stems creates all expected stem files."""
        from hypnogen.core.export import export_stems

        with tempfile.TemporaryDirectory() as tmpdir:
            stems_dir = os.path.join(tmpdir, "stems")
            
            shepherd = np.zeros((44100, 2), dtype=np.float32)
            weaver = np.zeros((44100, 2), dtype=np.float32)
            swarm = np.zeros((44100, 2), dtype=np.float32)
            bed = np.zeros((44100, 2), dtype=np.float32)
            mix = np.zeros((44100, 2), dtype=np.float32)
            
            export_stems(
                stems_dir,
                shepherd=shepherd,
                weaver=weaver,
                swarm=swarm,
                bed=bed,
                mix=mix,
            )

            assert os.path.exists(os.path.join(stems_dir, "shepherd.wav"))
            assert os.path.exists(os.path.join(stems_dir, "weaver.wav"))
            assert os.path.exists(os.path.join(stems_dir, "swarm.wav"))
            assert os.path.exists(os.path.join(stems_dir, "bed.wav"))
            assert os.path.exists(os.path.join(stems_dir, "mix.wav"))

    def test_skips_none_layers(self):
        """export_stems skips files for None layers."""
        from hypnogen.core.export import export_stems

        with tempfile.TemporaryDirectory() as tmpdir:
            stems_dir = os.path.join(tmpdir, "stems")
            
            shepherd = np.zeros((44100, 2), dtype=np.float32)
            
            export_stems(stems_dir, shepherd=shepherd)

            assert os.path.exists(os.path.join(stems_dir, "shepherd.wav"))
            assert not os.path.exists(os.path.join(stems_dir, "weaver.wav"))
            assert not os.path.exists(os.path.join(stems_dir, "swarm.wav"))
            assert not os.path.exists(os.path.join(stems_dir, "bed.wav"))
            assert not os.path.exists(os.path.join(stems_dir, "mix.wav"))

    def test_creates_directory_if_not_exists(self):
        """export_stems creates stems directory if it doesn't exist."""
        from hypnogen.core.export import export_stems

        with tempfile.TemporaryDirectory() as tmpdir:
            stems_dir = os.path.join(tmpdir, "nested", "stems", "dir")
            
            shepherd = np.zeros((44100, 2), dtype=np.float32)
            export_stems(stems_dir, shepherd=shepherd)

            assert os.path.isdir(stems_dir)
            assert os.path.exists(os.path.join(stems_dir, "shepherd.wav"))

    def test_empty_layers_writes_nothing(self):
        """export_stems with all None layers creates directory but no files."""
        from hypnogen.core.export import export_stems

        with tempfile.TemporaryDirectory() as tmpdir:
            stems_dir = os.path.join(tmpdir, "empty_stems")
            
            export_stems(stems_dir)

            assert os.path.isdir(stems_dir)
            assert len(os.listdir(stems_dir)) == 0


class TestCreateRenderMetadata:
    """Tests for create_render_metadata function."""

    def test_returns_dict_with_required_keys(self):
        """create_render_metadata returns dict with all required keys."""
        from hypnogen.core.export import create_render_metadata

        metadata = create_render_metadata(seed=42, duration_sec=600.0)

        assert "seed" in metadata
        assert "sample_rate" in metadata
        assert "duration_sec" in metadata
        assert "voices" in metadata
        assert "pitch_params" in metadata
        assert "gain_staging" in metadata
        assert "epoch_boundaries" in metadata
        assert "version" in metadata

    def test_uses_provided_values(self):
        """create_render_metadata uses provided values, not just defaults."""
        from hypnogen.core.export import create_render_metadata

        voices = {"shepherd": "af_heart", "weaver": "am_adam"}
        pitch_params = {"default_pitch": -2.0, "default_rate": 0.9}
        gain_staging = {"shepherd": -6, "weaver": -8, "swarm": -18, "bed": -12}
        epoch_boundaries = (0.0, 0.25, 0.55, 0.80, 1.0)

        metadata = create_render_metadata(
            seed=123,
            duration_sec=300.0,
            sr=48000,
            voices=voices,
            pitch_params=pitch_params,
            gain_staging=gain_staging,
            epoch_boundaries=epoch_boundaries,
            version="1.2.3",
        )

        assert metadata["seed"] == 123
        assert metadata["duration_sec"] == 300.0
        assert metadata["sample_rate"] == 48000
        assert metadata["voices"] == voices
        assert metadata["pitch_params"] == pitch_params
        assert metadata["gain_staging"] == gain_staging
        assert metadata["epoch_boundaries"] == list(epoch_boundaries)
        assert metadata["version"] == "1.2.3"

    def test_includes_version_number(self):
        """create_render_metadata includes version number."""
        from hypnogen.core.export import create_render_metadata

        metadata = create_render_metadata(seed=1, duration_sec=60.0)

        assert "version" in metadata
        assert metadata["version"] == "0.1.0"

    def test_epoch_boundaries_preserved_as_list(self):
        """create_render_metadata preserves epoch boundaries as list."""
        from hypnogen.core.export import create_render_metadata

        boundaries = (0.0, 0.2, 0.5, 0.85, 1.0)
        metadata = create_render_metadata(
            seed=1, duration_sec=60.0, epoch_boundaries=boundaries
        )

        assert metadata["epoch_boundaries"] == [0.0, 0.2, 0.5, 0.85, 1.0]
        assert isinstance(metadata["epoch_boundaries"], list)


class TestWriteMetadata:
    """Tests for write_metadata function."""

    def test_creates_valid_json_file(self):
        """write_metadata creates valid JSON file."""
        from hypnogen.core.export import write_metadata

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "render.json")
            metadata = {"seed": 42, "version": "0.1.0"}

            write_metadata(filepath, metadata)

            assert os.path.exists(filepath)
            with open(filepath, "r") as f:
                loaded = json.load(f)
            assert loaded == metadata

    def test_metadata_round_trip(self):
        """Write JSON, read it back, verify dict matches."""
        from hypnogen.core.export import create_render_metadata, write_metadata

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "render.json")
            
            metadata = create_render_metadata(
                seed=42,
                duration_sec=600.0,
                voices={"shepherd": "af_heart"},
                pitch_params={"default_pitch": -2.0},
                gain_staging={"shepherd": -6, "weaver": -8, "swarm": -18, "bed": -12},
            )

            write_metadata(filepath, metadata)

            with open(filepath, "r") as f:
                loaded = json.load(f)
            assert loaded == metadata

    def test_json_is_indented(self):
        """write_metadata uses indented JSON for readability."""
        from hypnogen.core.export import write_metadata

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "render.json")
            metadata = {"seed": 42, "nested": {"key": "value"}}

            write_metadata(filepath, metadata)

            with open(filepath, "r") as f:
                content = f.read()
            assert "\n" in content


class TestExportSession:
    """Tests for export_session function."""

    def test_exports_stems_and_metadata(self):
        """export_session exports stems AND metadata."""
        from hypnogen.core.export import create_render_metadata, export_session

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "session")
            
            shepherd = np.zeros((44100, 2), dtype=np.float32)
            mix = np.zeros((44100, 2), dtype=np.float32)
            metadata = create_render_metadata(seed=42, duration_sec=1.0)

            export_session(
                output_dir,
                metadata=metadata,
                shepherd=shepherd,
                mix=mix,
            )

            assert os.path.exists(os.path.join(output_dir, "shepherd.wav"))
            assert os.path.exists(os.path.join(output_dir, "mix.wav"))
            assert os.path.exists(os.path.join(output_dir, "render.json"))

            with open(os.path.join(output_dir, "render.json"), "r") as f:
                loaded = json.load(f)
            assert loaded["seed"] == 42

    def test_creates_output_directory_if_needed(self):
        """export_session creates output directory if it doesn't exist."""
        from hypnogen.core.export import create_render_metadata, export_session

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "nested", "output", "dir")
            
            metadata = create_render_metadata(seed=1, duration_sec=1.0)
            shepherd = np.zeros((44100, 2), dtype=np.float32)

            export_session(output_dir, metadata=metadata, shepherd=shepherd)

            assert os.path.isdir(output_dir)
            assert os.path.exists(os.path.join(output_dir, "render.json"))

    def test_only_writes_provided_stems(self):
        """export_session only writes provided stems (None layers skipped)."""
        from hypnogen.core.export import create_render_metadata, export_session

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "session")
            
            metadata = create_render_metadata(seed=1, duration_sec=1.0)
            shepherd = np.zeros((44100, 2), dtype=np.float32)

            export_session(output_dir, metadata=metadata, shepherd=shepherd)

            assert os.path.exists(os.path.join(output_dir, "shepherd.wav"))
            assert not os.path.exists(os.path.join(output_dir, "weaver.wav"))
            assert not os.path.exists(os.path.join(output_dir, "swarm.wav"))
            assert not os.path.exists(os.path.join(output_dir, "bed.wav"))
            assert not os.path.exists(os.path.join(output_dir, "mix.wav"))
            assert os.path.exists(os.path.join(output_dir, "render.json"))
