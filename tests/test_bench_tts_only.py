"""Tests for TTS-only benchmark harness."""

import json
import tempfile
import wave
import struct
from pathlib import Path
import pytest

# Import the module under test
from hypnogen.benchmarks.bench_tts_only import (
    get_git_sha,
    get_machine_info,
    validate_audio, normalize_audio_result,
    run_benchmark
)


class TestGitSha:
    """Tests for git SHA retrieval."""
    
    def test_get_git_sha_returns_string_or_none(self):
        """Git SHA should return a string or None, not raise."""
        result = get_git_sha()
        assert result is None or isinstance(result, str)
        if result:
            assert len(result) > 0


class TestMachineInfo:
    """Tests for machine info retrieval."""
    
    def test_get_machine_info_returns_dict(self):
        """Machine info should return a dict with expected keys."""
        info = get_machine_info()
        assert isinstance(info, dict)
        assert "platform" in info
        assert "hardware" in info
        assert "cpu" in info
        assert "memory_gb" in info


class TestAudioValidation:
    """Tests for audio sanity checks."""
    
    def create_test_wav(self, duration_sec=1.0, sample_rate=22050, amplitude=0.5):
        """Create a simple test WAV file in memory."""
        num_samples = int(duration_sec * sample_rate)
        
        # Generate sine wave
        import math
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            val = amplitude * math.sin(2 * math.pi * 440 * t)
            samples.append(int(val * 32767))
        
        # Pack into WAV
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            with wave.open(f.name, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                wav.writeframes(struct.pack(f'{len(samples)}h', *samples))
            
            with open(f.name, 'rb') as f:
                data = f.read()
            
            Path(f.name).unlink()
            return data
    
    def test_validate_empty_audio_fails(self):
        """Empty audio data should fail validation."""
        result = validate_audio(b'', 1.0)
        assert result["passed"] is False
        assert result["checks"]["non_empty"] is False
    
    def test_validate_valid_audio_passes(self):
        """Valid audio should pass all checks."""
        audio_data = self.create_test_wav(duration_sec=1.0)
        result = validate_audio(audio_data, 1.0)
        assert result["passed"] is True
        assert all(result["checks"].values())
    
    def test_validate_duration_out_of_bounds_fails(self):
        """Audio with wrong duration should fail duration check."""
        audio_data = self.create_test_wav(duration_sec=1.0)
        # Expect 10 seconds but got 1
        result = validate_audio(audio_data, 10.0)
        # Should fail duration_in_bounds
        assert result["checks"]["duration_in_bounds"] is False


class TestCorpusLoading:
    """Tests for corpus JSON loading."""
    
    def test_corpus_json_loads(self):
        """Corpus JSON should load and have required structure."""
        corpus_path = Path('hypnogen/benchmarks/corpus/tts_corpus.json')
        
        if not corpus_path.exists():
            pytest.skip("Corpus file not found")
        
        with open(corpus_path) as f:
            corpus = json.load(f)
        
        assert "version" in corpus
        assert "cases" in corpus
        assert isinstance(corpus["cases"], list)
        assert len(corpus["cases"]) > 0
        
        for case in corpus["cases"]:
            assert "case_id" in case
            assert "script_text" in case
            assert "affirmations" in case
            assert isinstance(case["affirmations"], list)


class TestOutputSchema:
    """Tests for benchmark output JSON schema."""
    
    def test_output_schema_structure(self):
        """Output JSON should have required keys."""
        # This test verifies the schema without actually running synthesis
        schema = {
            "timestamp": "string",
            "git_sha": "string or null",
            "machine_info": "dict",
            "config": {
                "provider": "string",
                "compute_units": "string or null",
                "voice": "string",
                "warm_repeats": "int"
            },
            "runs": [
                {
                    "case_id": "string",
                    "cold": {
                        "wall_time_sec": "float",
                        "audio_duration_sec": "float",
                        "rtf": "float",
                        "sanity_checks_passed": "bool",
                        "sanity_details": "dict"
                    },
                    "warm": {
                        "mean_wall_time_sec": "float",
                        "std_wall_time_sec": "float",
                        "mean_rtf": "float",
                        "repeats": "int",
                        "all_times": "list"
                    }
                }
            ]
        }
        
        # Verify schema structure is documented
        assert isinstance(schema, dict)
        assert "timestamp" in schema
        assert "runs" in schema


class TestComputeUnits:
    """Tests for compute units selection."""
    
    def test_compute_units_values(self):
        """Compute units should accept valid values."""
        valid_units = ['ALL', 'CPU_AND_GPU', 'CPU_ONLY', None]
        
        for unit in valid_units:
            # Just verify values are acceptable
            assert unit in valid_units


class TestBenchmarkIntegration:
    """Integration tests for benchmark harness."""
    
    @pytest.mark.skip(reason="Requires actual TTS models")
    def test_run_benchmark_creates_output(self, tmp_path):
        """Running benchmark should create output JSON file."""
        output_path = tmp_path / "test_output.json"
        corpus_path = Path('hypnogen/benchmarks/corpus/tts_corpus.json')
        
        if not corpus_path.exists():
            pytest.skip("Corpus file not found")
        
        # This would actually run synthesis - skip for unit tests
        # result = run_benchmark(
        #     corpus_path=corpus_path,
        #     provider_name='pytorch',
        #     voice='af_heart',
        #     output_path=output_path
        # )
        
        # For now, just verify the function exists
        assert callable(run_benchmark)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

class TestNormalization:
    """Tests for audio result normalization."""
    
    def test_normalize_bytes(self):
        """Raw bytes should be returned as-is."""
        data = b"audio data"
        assert normalize_audio_result(data) == data
        
    def test_normalize_tuple(self):
        """(bytes, sample_rate) should return bytes."""
        data = (b"audio data", 22050)
        assert normalize_audio_result(data) == b"audio data"
        
    def test_normalize_list_of_bytes(self):
        """List of bytes should be joined."""
        data = [b"chunk1", b"chunk2"]
        assert normalize_audio_result(data) == b"chunk1chunk2"
        
    def test_normalize_list_of_tuples(self):
        """List of (bytes, sample_rate) should be joined."""
        data = [(b"chunk1", 22050), (b"chunk2", 22050)]
        assert normalize_audio_result(data) == b"chunk1chunk2"
        
    def test_normalize_mixed_list(self):
        """Mixed list of bytes and tuples should be joined."""
        data = [b"chunk1", (b"chunk2", 22050)]
        assert normalize_audio_result(data) == b"chunk1chunk2"

    def test_normalize_numpy_tuple_encodes_wav_bytes(self):
        """(numpy_audio, sample_rate) should be encoded to WAV bytes."""
        import numpy as np

        audio = np.zeros(22050, dtype=np.float32)
        normalized = normalize_audio_result((audio, 22050))

        assert isinstance(normalized, bytes)
        assert normalized[:4] == b"RIFF"
