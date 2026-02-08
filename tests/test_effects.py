"""Tests for hypnogen.core.effects module.

Tests follow TDD approach: written before implementation.
"""

import numpy as np
import pytest

from hypnogen.core.effects import (
    apply_pitch_shift,
    apply_time_stretch,
    crossfade,
    apply_analog_marking,
)


class TestApplyPitchShift:
    """Test pitch shifting function."""

    def test_pitch_shift_preserves_duration(self):
        """Pitch shift should not significantly change audio duration."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        sr = 44100
        n_steps = -2.0

        result = apply_pitch_shift(audio, sr, n_steps)

        # Allow some tolerance (librosa may add/remove a few samples)
        assert abs(len(result) - len(audio)) <= 100

    def test_pitch_shift_zero_steps_preserves_audio(self):
        """Pitch shift with 0 steps should return approximately original audio."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        sr = 44100

        result = apply_pitch_shift(audio, sr, 0.0)

        # Should be very close to original (allow small numerical differences)
        assert len(result) == len(audio)
        # Check correlation is very high
        correlation = np.corrcoef(audio, result)[0, 1]
        assert correlation > 0.99

    def test_pitch_shift_no_nan_inf(self):
        """Pitch shift output should not contain NaN or Inf."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        sr = 44100
        n_steps = -3.0

        result = apply_pitch_shift(audio, sr, n_steps)

        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))

    def test_pitch_shift_negative_steps(self):
        """Pitch shift with negative steps should lower pitch."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        sr = 44100
        n_steps = -2.0

        result = apply_pitch_shift(audio, sr, n_steps)

        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32 or result.dtype == np.float64
        assert len(result) > 0

    def test_pitch_shift_positive_steps(self):
        """Pitch shift with positive steps should raise pitch."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        sr = 44100
        n_steps = 2.0

        result = apply_pitch_shift(audio, sr, n_steps)

        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32 or result.dtype == np.float64
        assert len(result) > 0


class TestApplyTimeStretch:
    """Test time stretching function."""

    def test_time_stretch_changes_duration(self):
        """Time stretch should change audio duration proportionally."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        rate = 2.0  # 2x speed = half duration

        result = apply_time_stretch(audio, rate)

        expected_length = int(len(audio) / rate)
        # Allow some tolerance
        assert abs(len(result) - expected_length) <= 100

    def test_time_stretch_rate_1_preserves_audio(self):
        """Time stretch with rate=1.0 should return approximately original audio."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))

        result = apply_time_stretch(audio, 1.0)

        # Should be very close to original
        assert len(result) == len(audio)
        correlation = np.corrcoef(audio, result)[0, 1]
        assert correlation > 0.99

    def test_time_stretch_no_nan_inf(self):
        """Time stretch output should not contain NaN or Inf."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        rate = 0.9

        result = apply_time_stretch(audio, rate)

        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))

    def test_time_stretch_slower(self):
        """Time stretch with rate < 1.0 should slow down audio (increase duration)."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        rate = 0.8  # Slower = longer

        result = apply_time_stretch(audio, rate)

        assert len(result) > len(audio)

    def test_time_stretch_faster(self):
        """Time stretch with rate > 1.0 should speed up audio (decrease duration)."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        rate = 1.5  # Faster = shorter

        result = apply_time_stretch(audio, rate)

        assert len(result) < len(audio)


class TestCrossfade:
    """Test crossfade function."""

    def test_crossfade_output_length(self):
        """Crossfade output length should be len(a) + len(b) - crossfade_samples."""
        audio_a = np.ones(10000)
        audio_b = np.ones(10000)
        crossfade_ms = 50
        sr = 44100

        result = crossfade(audio_a, audio_b, crossfade_ms, sr)

        crossfade_samples = int(crossfade_ms * sr / 1000)
        expected_length = len(audio_a) + len(audio_b) - crossfade_samples
        assert len(result) == expected_length

    def test_crossfade_zero_overlap_is_concatenation(self):
        """Crossfade with 0ms overlap should be simple concatenation."""
        audio_a = np.ones(1000) * 0.5
        audio_b = np.ones(1000) * -0.5
        crossfade_ms = 0
        sr = 44100

        result = crossfade(audio_a, audio_b, crossfade_ms, sr)

        expected = np.concatenate([audio_a, audio_b])
        np.testing.assert_array_almost_equal(result, expected)

    def test_crossfade_no_nan_inf(self):
        """Crossfade output should not contain NaN or Inf."""
        audio_a = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        audio_b = np.sin(2 * np.pi * 880 * np.linspace(0, 1, 44100))
        crossfade_ms = 50
        sr = 44100

        result = crossfade(audio_a, audio_b, crossfade_ms, sr)

        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))

    def test_crossfade_smooth_transition(self):
        """Crossfade should create smooth transition between segments."""
        # Create two distinct signals
        audio_a = np.ones(5000)
        audio_b = np.ones(5000) * -1.0
        crossfade_ms = 50
        sr = 44100

        result = crossfade(audio_a, audio_b, crossfade_ms, sr)

        # Check that crossfade region transitions smoothly
        crossfade_samples = int(crossfade_ms * sr / 1000)
        crossfade_start = len(audio_a) - crossfade_samples
        crossfade_region = result[crossfade_start:crossfade_start + crossfade_samples]

        # Should start near 1.0 and end near -1.0
        assert crossfade_region[0] > 0.5
        assert crossfade_region[-1] < -0.5

    def test_crossfade_short_segments(self):
        """Crossfade should handle short audio segments."""
        audio_a = np.ones(500)
        audio_b = np.ones(500)
        crossfade_ms = 10  # Short crossfade
        sr = 44100

        result = crossfade(audio_a, audio_b, crossfade_ms, sr)

        assert len(result) > 0
        assert not np.any(np.isnan(result))


class TestApplyAnalogMarking:
    """Test analog marking convenience function."""

    def test_apply_analog_marking_with_pitch_and_rate(self):
        """Analog marking should apply both pitch shift and time stretch."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        sr = 44100
        pitch_shift = -2.0
        rate = 0.9

        result = apply_analog_marking(audio, sr, pitch_shift, rate)

        # Output should be valid
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))

        # Duration should change due to time stretch
        expected_length = int(len(audio) / rate)
        assert abs(len(result) - expected_length) <= 100

    def test_apply_analog_marking_defaults_preserve_audio(self):
        """Analog marking with defaults (pitch=0, rate=1.0) should preserve audio."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        sr = 44100

        result = apply_analog_marking(audio, sr)

        assert len(result) == len(audio)
        correlation = np.corrcoef(audio, result)[0, 1]
        assert correlation > 0.99

    def test_apply_analog_marking_no_nan_inf(self):
        """Analog marking output should not contain NaN or Inf."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        sr = 44100
        pitch_shift = -3.0
        rate = 0.85

        result = apply_analog_marking(audio, sr, pitch_shift, rate)

        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))

    def test_apply_analog_marking_pitch_only(self):
        """Analog marking with only pitch shift (rate=1.0)."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        sr = 44100
        pitch_shift = -2.0

        result = apply_analog_marking(audio, sr, pitch_shift=pitch_shift, rate=1.0)

        # Duration should be preserved
        assert abs(len(result) - len(audio)) <= 100
        assert not np.any(np.isnan(result))

    def test_apply_analog_marking_rate_only(self):
        """Analog marking with only time stretch (pitch=0.0)."""
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        sr = 44100
        rate = 0.9

        result = apply_analog_marking(audio, sr, pitch_shift=0.0, rate=rate)

        # Duration should change
        expected_length = int(len(audio) / rate)
        assert abs(len(result) - expected_length) <= 100
        assert not np.any(np.isnan(result))

    def test_apply_analog_marking_different_sample_rates(self):
        """Analog marking should work with different sample rates."""
        # Test with TTS output rate (24000 Hz)
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 24000))
        sr = 24000
        pitch_shift = -2.0
        rate = 0.9

        result = apply_analog_marking(audio, sr, pitch_shift, rate)

        assert isinstance(result, np.ndarray)
        assert len(result) > 0
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))
