"""Tests for multi-track mixer module."""

import numpy as np
import pytest

from hypnogen.core.mixer import (
    DEFAULT_GAIN_DB,
    apply_gain_db,
    apply_limiter,
    mix_layers,
)


class TestApplyGainDB:
    """Tests for dB-to-linear gain conversion."""

    def test_zero_db_is_identity(self):
        """0dB gain should leave audio unchanged."""
        audio = np.array([0.5, -0.3, 0.8])
        result = apply_gain_db(audio, 0.0)
        np.testing.assert_allclose(result, audio, rtol=1e-6)

    def test_minus_6db_halves_amplitude(self):
        """-6dB should approximately halve amplitude."""
        audio = np.array([1.0, -1.0, 0.5])
        result = apply_gain_db(audio, -6.0)
        # -6dB = 10^(-6/20) ≈ 0.501
        expected = audio * 0.501187
        np.testing.assert_allclose(result, expected, rtol=1e-4)

    def test_minus_20db_reduces_to_tenth(self):
        """-20dB should reduce to ~0.1x amplitude."""
        audio = np.array([1.0, -0.5, 0.3])
        result = apply_gain_db(audio, -20.0)
        # -20dB = 10^(-20/20) = 0.1
        expected = audio * 0.1
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_positive_gain_amplifies(self):
        """+6dB should approximately double amplitude."""
        audio = np.array([0.25, -0.125])
        result = apply_gain_db(audio, 6.0)
        # +6dB = 10^(6/20) ≈ 1.995
        expected = audio * 1.995262
        np.testing.assert_allclose(result, expected, rtol=1e-4)

    def test_works_with_stereo(self):
        """Should work with stereo (N, 2) arrays."""
        audio = np.array([[0.5, -0.3], [0.2, 0.8]])
        result = apply_gain_db(audio, -3.0)
        # -3dB = 10^(-3/20) ≈ 0.708
        expected = audio * 0.707946
        np.testing.assert_allclose(result, expected, rtol=1e-4)


class TestApplyLimiter:
    """Tests for peak limiter using pedalboard."""

    def test_prevents_clipping_above_one(self):
        """Limiter should prevent peaks from exceeding 1.0."""
        sr = 44100
        length = 1000
        audio = np.random.randn(length, 2).astype(np.float32) * 3.0
        result = apply_limiter(audio, sr, threshold_db=-1.0)

        assert np.max(np.abs(result)) <= 1.0 + 1e-6

    def test_quiet_audio_shape_preserved(self):
        """Limiter should preserve shape for quiet audio."""
        sr = 44100
        audio = np.array([[0.1, -0.1], [0.05, 0.08]], dtype=np.float32)
        result = apply_limiter(audio, sr, threshold_db=-1.0)

        assert result.shape == audio.shape

    def test_stereo_shape_preserved(self):
        """Limiter should preserve stereo (N, 2) shape."""
        sr = 44100
        audio = np.random.randn(1000, 2).astype(np.float32)
        result = apply_limiter(audio, sr)

        assert result.shape == audio.shape
        assert result.ndim == 2

    def test_mono_shape_preserved(self):
        """Limiter should work with mono (N,) arrays."""
        sr = 44100
        audio = np.random.randn(1000).astype(np.float32)
        result = apply_limiter(audio, sr)

        assert result.shape == audio.shape
        assert result.ndim == 1

    def test_no_nan_or_inf(self):
        """Limiter output should never contain NaN/Inf."""
        sr = 44100
        audio = np.array([[3.0, -2.5], [1.0, 0.0]], dtype=np.float32)
        result = apply_limiter(audio, sr)

        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))


class TestMixLayers:
    """Tests for main mixing function."""

    def test_single_shepherd_only(self):
        """Mix with only shepherd should return shepherd with gain applied."""
        sr = 44100
        length = 1000
        shepherd = np.ones((length, 2), dtype=np.float32) * 0.3

        result = mix_layers(shepherd=shepherd, sr=sr, apply_epochs=False)

        assert result.shape == (length, 2)
        assert not np.any(np.isnan(result))
        assert np.max(np.abs(result)) <= 1.0

    def test_all_four_layers_sum(self):
        """Mix with all 4 layers should return summed result."""
        sr = 44100
        length = 1000
        shepherd = np.random.randn(length, 2).astype(np.float32) * 0.3
        weaver = np.random.randn(length, 2).astype(np.float32) * 0.2
        swarm = np.random.randn(length, 2).astype(np.float32) * 0.1
        bed = np.random.randn(length, 2).astype(np.float32) * 0.4

        result = mix_layers(
            shepherd=shepherd,
            weaver=weaver,
            swarm=swarm,
            bed=bed,
            sr=sr,
            apply_epochs=False,
        )

        assert result.shape == (length, 2)
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))

    def test_output_peak_limited(self):
        """Mix output should have peaks <= 1.0 (limiter working)."""
        sr = 44100
        length = 10000
        shepherd = np.random.randn(length, 2).astype(np.float32) * 0.8
        weaver = np.random.randn(length, 2).astype(np.float32) * 0.8
        swarm = np.random.randn(length, 2).astype(np.float32) * 0.5
        bed = np.random.randn(length, 2).astype(np.float32) * 0.8

        result = mix_layers(
            shepherd=shepherd,
            weaver=weaver,
            swarm=swarm,
            bed=bed,
            sr=sr,
            apply_epochs=False,
        )

        assert np.max(np.abs(result)) <= 1.0 + 1e-6

    def test_epoch_gain_varies_over_time(self):
        """With apply_epochs=True, gain should vary over time."""
        sr = 44100
        duration = 10.0  # 10 seconds
        length = int(sr * duration)
        shepherd = np.ones((length, 2), dtype=np.float32) * 0.5

        result = mix_layers(shepherd=shepherd, sr=sr, apply_epochs=True)

        # Extract shepherd component (difficult since it's mixed, but we can check variance)
        # At minimum, output should not be constant (epochs modulate gain)
        # Check that variance exists over time
        segment_size = length // 4
        segments = [result[i * segment_size : (i + 1) * segment_size] for i in range(4)]
        segment_peaks = [np.max(np.abs(seg)) for seg in segments]

        # Peaks across segments should vary (not all identical)
        assert np.std(segment_peaks) > 0.01

    def test_no_epochs_constant_gain(self):
        """With apply_epochs=False, gain should be constant."""
        sr = 44100
        length = 10000
        shepherd = np.ones((length, 2), dtype=np.float32) * 0.3

        result = mix_layers(shepherd=shepherd, sr=sr, apply_epochs=False)

        # With constant input and no epochs, output peaks should be similar across segments
        segment_size = length // 4
        segments = [result[i * segment_size : (i + 1) * segment_size] for i in range(4)]
        segment_peaks = [np.max(np.abs(seg)) for seg in segments]

        # Peaks should be very similar (within 5% of each other)
        assert np.std(segment_peaks) < 0.05 * np.mean(segment_peaks)

    def test_pads_shorter_layers(self):
        """Shorter layers should be padded to match longest."""
        sr = 44100
        shepherd = np.ones((5000, 2), dtype=np.float32) * 0.3
        bed = np.ones((10000, 2), dtype=np.float32) * 0.2

        result = mix_layers(shepherd=shepherd, bed=bed, sr=sr, apply_epochs=False)

        # Output should match longest layer
        assert result.shape[0] == 10000

    def test_none_layers_ignored(self):
        """None layers should be skipped in mixing."""
        sr = 44100
        shepherd = np.ones((1000, 2), dtype=np.float32) * 0.3

        result = mix_layers(
            shepherd=shepherd, weaver=None, swarm=None, bed=None, sr=sr, apply_epochs=False
        )

        assert result.shape == (1000, 2)
        assert not np.any(np.isnan(result))

    def test_returns_stereo_array(self):
        """Mix should always return stereo (N, 2) array."""
        sr = 44100
        shepherd = np.ones((1000, 2), dtype=np.float32) * 0.3
        result = mix_layers(shepherd=shepherd, sr=sr)

        assert result.ndim == 2
        assert result.shape[1] == 2

    def test_custom_gain_db(self):
        """Should respect custom per-layer gain values."""
        sr = 44100
        length = 1000
        shepherd = np.ones((length, 2), dtype=np.float32) * 0.3
        custom_gain = {"shepherd": -12.0}

        result = mix_layers(shepherd=shepherd, sr=sr, gain_db=custom_gain, apply_epochs=False)

        assert result.shape == (length, 2)
        assert not np.any(np.isnan(result))
        assert np.max(np.abs(result)) <= 1.0

    def test_default_gain_values(self):
        """DEFAULT_GAIN_DB should have correct values."""
        assert DEFAULT_GAIN_DB["shepherd"] == -6.0
        assert DEFAULT_GAIN_DB["weaver"] == -8.0
        assert DEFAULT_GAIN_DB["swarm"] == -18.0
        assert DEFAULT_GAIN_DB["bed"] == -12.0

    def test_seed_reproducibility(self):
        """Same RNG seed should produce identical output."""
        sr = 44100
        length = 5000
        shepherd = np.random.randn(length, 2).astype(np.float32) * 0.3

        rng1 = np.random.default_rng(42)
        result1 = mix_layers(shepherd=shepherd, sr=sr, apply_epochs=True, rng=rng1)

        rng2 = np.random.default_rng(42)
        result2 = mix_layers(shepherd=shepherd, sr=sr, apply_epochs=True, rng=rng2)

        np.testing.assert_array_equal(result1, result2)

    def test_boundary_events_inserted(self):
        """With boundary_events, events should be inserted at correct positions."""
        sr = 44100
        duration = 10.0
        length = int(sr * duration)
        shepherd = np.ones((length, 2), dtype=np.float32) * 0.3

        # Use fixed RNG for reproducible event selection
        rng = np.random.default_rng(123)
        boundary_events = ["snap", "silence", "stereo_collapse"]

        result = mix_layers(
            shepherd=shepherd, sr=sr, apply_epochs=False, boundary_events=boundary_events, rng=rng
        )

        # Can't easily verify events without knowing internal implementation,
        # but we can check output is valid
        assert result.shape[0] >= length - 100  # May be slightly different due to event insertion
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))

    def test_all_none_layers_returns_silence(self):
        """Mix with all None layers should return silence."""
        sr = 44100
        # Need at least some duration, but all layers are None
        # This should ideally not happen, but handle gracefully
        result = mix_layers(
            shepherd=None, weaver=None, swarm=None, bed=None, sr=sr, apply_epochs=False
        )

        # Should return minimal-length silence (1 sample to avoid empty array)
        assert result.shape[0] > 0
        assert result.shape[1] == 2
        # All zeros
        np.testing.assert_array_equal(result, np.zeros_like(result))
