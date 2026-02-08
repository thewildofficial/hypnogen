"""Tests for binaural beat generation module."""

import numpy as np
import pytest


class TestGenerateBinauralBeat:
    """Tests for generate_binaural_beat function."""

    def test_duration_matches_expected_shape(self):
        """10 seconds at 44100Hz should produce 441000 samples."""
        from hypnogen.core.binaural import generate_binaural_beat
        
        result = generate_binaural_beat(duration_sec=10.0, sr=44100)
        
        expected_samples = 441000
        assert result.shape == (expected_samples, 2), \
            f"Expected shape ({expected_samples}, 2), got {result.shape}"

    def test_output_is_stereo(self):
        """Output should be stereo (N, 2) array."""
        from hypnogen.core.binaural import generate_binaural_beat
        
        result = generate_binaural_beat(duration_sec=1.0)
        
        assert result.ndim == 2, f"Expected 2D array, got {result.ndim}D"
        assert result.shape[1] == 2, f"Expected 2 channels, got {result.shape[1]}"

    def test_values_normalized_no_clipping(self):
        """All values should be in range [-1.0, 1.0]."""
        from hypnogen.core.binaural import generate_binaural_beat
        
        result = generate_binaural_beat(duration_sec=5.0)
        
        max_val = np.max(np.abs(result))
        assert max_val <= 1.0, f"Peak value {max_val} exceeds 1.0 (clipping detected)"

    def test_no_nan_or_inf_in_output(self):
        """Output should contain no NaN or Inf values."""
        from hypnogen.core.binaural import generate_binaural_beat
        
        result = generate_binaural_beat(duration_sec=3.0)
        
        assert not np.any(np.isnan(result)), "NaN values detected in output"
        assert not np.any(np.isinf(result)), "Inf values detected in output"

    def test_deterministic_output(self):
        """Binaural beats are deterministic (no randomness)."""
        from hypnogen.core.binaural import generate_binaural_beat
        
        result1 = generate_binaural_beat(duration_sec=2.0)
        result2 = generate_binaural_beat(duration_sec=2.0)
        
        np.testing.assert_array_equal(result1, result2, 
                                       err_msg="Same parameters produced different outputs")

    def test_very_short_duration(self):
        """Edge case: very short duration (0.1s) should work."""
        from hypnogen.core.binaural import generate_binaural_beat
        
        result = generate_binaural_beat(duration_sec=0.1, sr=44100)
        
        expected_samples = 4410
        assert result.shape == (expected_samples, 2)
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))

    def test_constant_beat_frequency(self):
        """Edge case: start_beat == end_beat should work (no ramp)."""
        from hypnogen.core.binaural import generate_binaural_beat
        
        result = generate_binaural_beat(
            duration_sec=1.0, 
            start_beat_freq=10, 
            end_beat_freq=10
        )
        
        assert result.shape[1] == 2
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))


class TestGeneratePinkNoise:
    """Tests for generate_pink_noise function."""

    def test_correct_length(self):
        """Pink noise should have the requested number of samples."""
        from hypnogen.core.binaural import generate_pink_noise
        
        num_samples = 44100
        result = generate_pink_noise(num_samples)
        
        assert len(result) == num_samples

    def test_output_is_mono(self):
        """Output should be mono (1D array)."""
        from hypnogen.core.binaural import generate_pink_noise
        
        result = generate_pink_noise(10000)
        
        assert result.ndim == 1, f"Expected 1D array, got {result.ndim}D"

    def test_no_nan_or_inf_in_pink_noise(self):
        """Pink noise should contain no NaN or Inf values."""
        from hypnogen.core.binaural import generate_pink_noise
        
        result = generate_pink_noise(44100)
        
        assert not np.any(np.isnan(result)), "NaN values detected in pink noise"
        assert not np.any(np.isinf(result)), "Inf values detected in pink noise"

    def test_pink_noise_seed_reproducibility(self):
        """Same seed should produce identical pink noise."""
        from hypnogen.core.binaural import generate_pink_noise
        
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        result1 = generate_pink_noise(10000, rng=rng1)
        result2 = generate_pink_noise(10000, rng=rng2)
        
        np.testing.assert_array_equal(result1, result2,
                                       err_msg="Same seed produced different pink noise")

    def test_pink_noise_different_seeds(self):
        """Different seeds should produce different pink noise."""
        from hypnogen.core.binaural import generate_pink_noise
        
        result1 = generate_pink_noise(10000, rng=np.random.default_rng(42))
        result2 = generate_pink_noise(10000, rng=np.random.default_rng(99))
        
        assert not np.array_equal(result1, result2), \
            "Different seeds produced identical pink noise"

    def test_pink_noise_normalized(self):
        """Pink noise should be normalized to [-1.0, 1.0]."""
        from hypnogen.core.binaural import generate_pink_noise
        
        result = generate_pink_noise(44100)
        
        max_val = np.max(np.abs(result))
        assert max_val <= 1.0, f"Pink noise peak {max_val} exceeds 1.0"


class TestGenerateBed:
    """Tests for generate_bed function (binaural + pink noise)."""

    def test_bed_correct_shape(self):
        """Bed should be stereo (N, 2) array with correct duration."""
        from hypnogen.core.binaural import generate_bed
        
        result = generate_bed(duration_sec=5.0, sr=44100)
        
        expected_samples = 220500
        assert result.shape == (expected_samples, 2)

    def test_bed_no_clipping(self):
        """Combined bed should not clip (values <= 1.0)."""
        from hypnogen.core.binaural import generate_bed
        
        result = generate_bed(duration_sec=3.0)
        
        max_val = np.max(np.abs(result))
        assert max_val <= 1.0, f"Bed peak {max_val} exceeds 1.0 (clipping detected)"

    def test_bed_no_nan_or_inf(self):
        """Bed should contain no NaN or Inf values."""
        from hypnogen.core.binaural import generate_bed
        
        result = generate_bed(duration_sec=2.0)
        
        assert not np.any(np.isnan(result)), "NaN values detected in bed"
        assert not np.any(np.isinf(result)), "Inf values detected in bed"

    def test_bed_seed_reproducibility(self):
        """Same seed should produce identical bed."""
        from hypnogen.core.binaural import generate_bed
        
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        result1 = generate_bed(duration_sec=1.0, rng=rng1)
        result2 = generate_bed(duration_sec=1.0, rng=rng2)
        
        np.testing.assert_array_equal(result1, result2,
                                       err_msg="Same seed produced different bed")

    def test_bed_different_seeds(self):
        """Different seeds should produce different bed."""
        from hypnogen.core.binaural import generate_bed
        
        result1 = generate_bed(duration_sec=1.0, rng=np.random.default_rng(42))
        result2 = generate_bed(duration_sec=1.0, rng=np.random.default_rng(99))
        
        assert not np.array_equal(result1, result2), \
            "Different seeds produced identical bed"

    def test_bed_with_zero_pink_noise(self):
        """Bed with pink_noise_level=0 should equal pure binaural beat."""
        from hypnogen.core.binaural import generate_bed, generate_binaural_beat
        
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        bed = generate_bed(duration_sec=1.0, pink_noise_level=0.0, rng=rng1)
        binaural = generate_binaural_beat(duration_sec=1.0, rng=rng2)
        
        # Should be very close (allowing for numerical precision)
        np.testing.assert_array_almost_equal(bed, binaural, decimal=10)

    def test_bed_very_short_duration(self):
        """Edge case: very short duration should work for bed."""
        from hypnogen.core.binaural import generate_bed
        
        result = generate_bed(duration_sec=0.1)
        
        expected_samples = 4410
        assert result.shape == (expected_samples, 2)
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))
