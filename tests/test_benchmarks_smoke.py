"""Smoke tests for benchmark harness and comparison utility."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest


class TestBenchRender:
    """Smoke tests for bench_render module."""

    @pytest.fixture
    def mock_synthesize(self):
        """Mock TTS and effects to avoid model download and heavy DSP."""
        mock_audio = np.zeros(24000, dtype=np.float32)
        with patch("hypnogen.benchmarks.bench_render.synthesize") as mock_tts, \
             patch("hypnogen.core.effects.apply_pitch_shift", side_effect=lambda a, sr, n: a.copy()), \
             patch("hypnogen.core.effects.apply_time_stretch", side_effect=lambda a, r: a.copy()):
            mock_tts.return_value = (mock_audio, 24000)
            yield mock_tts

    def test_benchmark_fixtures_exist(self):
        """Benchmark module exposes deterministic fixtures."""
        from hypnogen.benchmarks.bench_render import FIXTURE_SCRIPT, FIXTURE_AFFIRMATIONS, FIXTURE_VOICE, FIXTURE_SEED

        assert isinstance(FIXTURE_SCRIPT, str)
        assert len(FIXTURE_SCRIPT) > 0
        assert isinstance(FIXTURE_AFFIRMATIONS, list)
        assert len(FIXTURE_AFFIRMATIONS) >= 2
        assert isinstance(FIXTURE_VOICE, str)
        assert isinstance(FIXTURE_SEED, int)

    def test_run_benchmark_returns_result_dict(self, mock_synthesize):
        """run_benchmark returns dict with required keys."""
        from hypnogen.benchmarks.bench_render import run_benchmark

        with tempfile.TemporaryDirectory() as tmpdir:
            out_wav = str(Path(tmpdir) / "bench.wav")
            result = run_benchmark(out_path=out_wav)

        assert isinstance(result, dict)
        assert "total_sec" in result
        assert "stages" in result
        assert "config_hash" in result
        assert "git_sha" in result
        assert "timestamp" in result

    def test_run_benchmark_captures_stage_timings(self, mock_synthesize):
        """Per-stage timings are captured in result."""
        from hypnogen.benchmarks.bench_render import run_benchmark

        with tempfile.TemporaryDirectory() as tmpdir:
            out_wav = str(Path(tmpdir) / "bench.wav")
            result = run_benchmark(out_path=out_wav)

        stages = result["stages"]
        expected_stages = ["parse", "tts", "mix", "export"]
        for stage in expected_stages:
            assert stage in stages, f"Missing stage: {stage}"
            assert isinstance(stages[stage], float)
            assert stages[stage] >= 0

    def test_run_benchmark_creates_wav(self, mock_synthesize):
        """Benchmark creates output WAV file."""
        from hypnogen.benchmarks.bench_render import run_benchmark

        with tempfile.TemporaryDirectory() as tmpdir:
            out_wav = str(Path(tmpdir) / "bench.wav")
            run_benchmark(out_path=out_wav)
            assert Path(out_wav).exists()

    def test_run_benchmark_writes_json(self, mock_synthesize):
        """Benchmark writes valid JSON result file."""
        from hypnogen.benchmarks.bench_render import run_benchmark

        with tempfile.TemporaryDirectory() as tmpdir:
            out_wav = str(Path(tmpdir) / "bench.wav")
            json_path = str(Path(tmpdir) / "result.json")
            run_benchmark(out_path=out_wav, json_path=json_path)

            assert Path(json_path).exists()
            with open(json_path) as f:
                data = json.load(f)
            assert "total_sec" in data
            assert "stages" in data

    def test_run_benchmark_deterministic_config_hash(self, mock_synthesize):
        """Same fixtures produce same config hash."""
        from hypnogen.benchmarks.bench_render import run_benchmark

        with tempfile.TemporaryDirectory() as tmpdir:
            r1 = run_benchmark(out_path=str(Path(tmpdir) / "a.wav"))
            r2 = run_benchmark(out_path=str(Path(tmpdir) / "b.wav"))

        assert r1["config_hash"] == r2["config_hash"]

    def test_total_sec_equals_sum_of_stages(self, mock_synthesize):
        """total_sec should be close to sum of stage timings."""
        from hypnogen.benchmarks.bench_render import run_benchmark

        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_benchmark(out_path=str(Path(tmpdir) / "bench.wav"))

        stage_sum = sum(result["stages"].values())
        # total_sec includes minor overhead, so allow some slack
        assert result["total_sec"] >= stage_sum * 0.9


class TestCompare:
    """Smoke tests for comparison utility."""

    def test_compare_two_results(self):
        """compare_results returns deltas between two benchmark results."""
        from hypnogen.benchmarks.compare import compare_results

        baseline = {
            "total_sec": 10.0,
            "stages": {"parse": 0.1, "tts": 8.0, "mix": 1.5, "export": 0.4},
            "config_hash": "abc123",
        }
        current = {
            "total_sec": 8.5,
            "stages": {"parse": 0.1, "tts": 6.5, "mix": 1.5, "export": 0.4},
            "config_hash": "abc123",
        }

        deltas = compare_results(baseline, current)
        assert "total_sec" in deltas
        assert deltas["total_sec"]["delta"] == pytest.approx(-1.5)
        assert "stages" in deltas
        assert deltas["stages"]["tts"]["delta"] == pytest.approx(-1.5)

    def test_compare_formats_output(self):
        """format_comparison returns human-readable string."""
        from hypnogen.benchmarks.compare import compare_results, format_comparison

        baseline = {
            "total_sec": 10.0,
            "stages": {"parse": 0.1, "tts": 8.0, "mix": 1.5, "export": 0.4},
            "config_hash": "abc123",
        }
        current = {
            "total_sec": 8.5,
            "stages": {"parse": 0.1, "tts": 6.5, "mix": 1.5, "export": 0.4},
            "config_hash": "abc123",
        }

        deltas = compare_results(baseline, current)
        output = format_comparison(deltas)
        assert isinstance(output, str)
        assert "total" in output.lower()
        assert "tts" in output.lower()

    def test_compare_warns_on_config_mismatch(self):
        """compare_results flags mismatched config hashes."""
        from hypnogen.benchmarks.compare import compare_results

        baseline = {
            "total_sec": 10.0,
            "stages": {"parse": 0.1},
            "config_hash": "abc123",
        }
        current = {
            "total_sec": 9.0,
            "stages": {"parse": 0.1},
            "config_hash": "different",
        }

        deltas = compare_results(baseline, current)
        assert deltas.get("config_mismatch") is True
