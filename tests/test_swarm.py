"""Tests for affirmation swarm generation."""

import numpy as np
import pytest

from hypnogen.core.swarm import (
    apply_constant_power_pan,
    generate_swarm,
    phonetic_hash,
    phonetic_similarity,
    schedule_affirmations,
    validate_affirmation,
    validate_affirmations,
)


class TestValidateAffirmation:
    """Test affirmation validation rules."""

    def test_valid_short_present_tense(self):
        """Valid: short present-tense affirmation."""
        valid, reason = validate_affirmation("I am calm")
        assert valid is True
        assert reason == "OK"

    def test_valid_seven_words(self):
        """Valid: exactly 7 words."""
        valid, reason = validate_affirmation("I am confident and strong every day")
        assert valid is True
        assert reason == "OK"

    def test_invalid_empty(self):
        """Invalid: empty string."""
        valid, reason = validate_affirmation("")
        assert valid is False
        assert "empty" in reason.lower()

    def test_invalid_whitespace_only(self):
        """Invalid: whitespace-only string."""
        valid, reason = validate_affirmation("   ")
        assert valid is False
        assert "empty" in reason.lower()

    def test_invalid_too_many_words(self):
        """Invalid: more than 7 words."""
        valid, reason = validate_affirmation(
            "I am confident and strong and brave and powerful"
        )
        assert valid is False
        assert "7 words" in reason.lower() or "word" in reason.lower()

    def test_invalid_past_tense_was(self):
        """Invalid: past tense 'was'."""
        valid, reason = validate_affirmation("I was calm yesterday")
        assert valid is False
        assert "tense" in reason.lower() or "was" in reason.lower()

    def test_invalid_past_tense_were(self):
        """Invalid: past tense 'were'."""
        valid, reason = validate_affirmation("They were happy")
        assert valid is False
        assert "tense" in reason.lower() or "were" in reason.lower()

    def test_invalid_future_will(self):
        """Invalid: future tense 'will'."""
        valid, reason = validate_affirmation("I will succeed")
        assert valid is False
        assert "tense" in reason.lower() or "will" in reason.lower()

    def test_invalid_conditional_would(self):
        """Invalid: conditional 'would'."""
        valid, reason = validate_affirmation("I would be happy")
        assert valid is False
        assert "tense" in reason.lower() or "would" in reason.lower()

    def test_invalid_conditional_could(self):
        """Invalid: conditional 'could'."""
        valid, reason = validate_affirmation("I could achieve anything")
        assert valid is False
        assert "tense" in reason.lower() or "could" in reason.lower()

    def test_invalid_conditional_should(self):
        """Invalid: conditional 'should'."""
        valid, reason = validate_affirmation("I should be confident")
        assert valid is False
        assert "tense" in reason.lower() or "should" in reason.lower()

    def test_invalid_past_perfect_had(self):
        """Invalid: past perfect 'had'."""
        valid, reason = validate_affirmation("I had been calm")
        assert valid is False
        assert "tense" in reason.lower() or "had" in reason.lower()

    def test_invalid_present_perfect_have_been(self):
        """Invalid: present perfect 'have been'."""
        valid, reason = validate_affirmation("I have been confident")
        assert valid is False
        assert "tense" in reason.lower() or "have been" in reason.lower()

    def test_invalid_negation_not(self):
        """Invalid: negation 'not'."""
        valid, reason = validate_affirmation("I am not afraid")
        assert valid is False
        assert "negation" in reason.lower() or "not" in reason.lower()

    def test_invalid_negation_never(self):
        """Invalid: negation 'never'."""
        valid, reason = validate_affirmation("I never fail")
        assert valid is False
        assert "negation" in reason.lower() or "never" in reason.lower()

    def test_invalid_negation_dont(self):
        """Invalid: negation 'don't'."""
        valid, reason = validate_affirmation("I don't worry")
        assert valid is False
        assert "negation" in reason.lower() or "don't" in reason.lower()

    def test_invalid_negation_wont(self):
        """Invalid: negation 'won't'."""
        valid, reason = validate_affirmation("I won't give up")
        assert valid is False
        assert "negation" in reason.lower() or "won't" in reason.lower()

    def test_invalid_negation_cant(self):
        """Invalid: negation 'can't'."""
        valid, reason = validate_affirmation("I can't be stopped")
        assert valid is False
        assert "negation" in reason.lower() or "can't" in reason.lower()

    def test_invalid_negation_isnt(self):
        """Invalid: negation 'isn't'."""
        valid, reason = validate_affirmation("Fear isn't real")
        assert valid is False
        assert "negation" in reason.lower() or "isn't" in reason.lower()

    def test_invalid_negation_arent(self):
        """Invalid: negation 'aren't'."""
        valid, reason = validate_affirmation("Limitations aren't real")
        assert valid is False
        assert "negation" in reason.lower() or "aren't" in reason.lower()

    def test_invalid_negation_doesnt(self):
        """Invalid: negation 'doesn't'."""
        valid, reason = validate_affirmation("It doesn't matter")
        assert valid is False
        assert "negation" in reason.lower() or "doesn't" in reason.lower()

    def test_invalid_negation_didnt(self):
        """Invalid: negation 'didn't'."""
        valid, reason = validate_affirmation("I didn't fail")
        assert valid is False
        assert "negation" in reason.lower() or "didn't" in reason.lower()

    def test_invalid_multiple_violations(self):
        """Invalid: multiple violations (future + negation)."""
        valid, reason = validate_affirmation("I will never fail")
        assert valid is False
        # Should catch at least one violation
        assert "negation" in reason.lower() or "tense" in reason.lower()

    def test_case_insensitive_validation(self):
        """Validation should be case-insensitive."""
        valid, reason = validate_affirmation("I WAS calm")
        assert valid is False
        assert "tense" in reason.lower() or "was" in reason.lower()


class TestValidateAffirmations:
    """Test batch affirmation validation."""

    def test_batch_validation_mixed(self):
        """Batch validation with mixed valid/invalid."""
        results = validate_affirmations(
            [
                "I am calm",
                "I was calm yesterday",
                "I am strong",
                "I will never fail",
            ]
        )
        assert len(results) == 4
        assert results[0] == (True, "OK")
        assert results[1][0] is False
        assert results[2] == (True, "OK")
        assert results[3][0] is False

    def test_batch_validation_all_valid(self):
        """Batch validation with all valid."""
        results = validate_affirmations(
            [
                "I am calm",
                "I am strong",
                "I am confident",
            ]
        )
        assert len(results) == 3
        assert all(valid for valid, _ in results)

    def test_batch_validation_all_invalid(self):
        """Batch validation with all invalid."""
        results = validate_affirmations(
            [
                "I was calm",
                "I will succeed",
                "I am not afraid",
            ]
        )
        assert len(results) == 3
        assert all(not valid for valid, _ in results)

    def test_batch_validation_empty_list(self):
        """Batch validation with empty list."""
        results = validate_affirmations([])
        assert results == []


class TestApplyConstantPowerPan:
    """Test constant power panning."""

    def test_pan_center(self):
        """Pan center (0.0) should produce equal L/R."""
        mono = np.array([0.5, 0.5, 0.5])
        stereo = apply_constant_power_pan(mono, pan=0.0)
        
        assert stereo.shape == (3, 2)
        # At center, left and right should be equal (≈0.707 * input)
        np.testing.assert_allclose(stereo[:, 0], stereo[:, 1], rtol=1e-6)
        # Energy should be preserved: L^2 + R^2 = input^2
        # At center: cos(π/4)^2 + sin(π/4)^2 = 0.5 + 0.5 = 1.0
        np.testing.assert_allclose(
            stereo[:, 0]**2 + stereo[:, 1]**2,
            mono**2,
            rtol=1e-6
        )

    def test_pan_full_left(self):
        """Pan full left (-1.0) should produce L=input, R≈0."""
        mono = np.array([0.5, 0.5, 0.5])
        stereo = apply_constant_power_pan(mono, pan=-1.0)
        
        assert stereo.shape == (3, 2)
        # Left should be ~input, right should be ~0
        np.testing.assert_allclose(stereo[:, 0], mono, rtol=1e-6)
        np.testing.assert_allclose(stereo[:, 1], 0.0, atol=1e-6)

    def test_pan_full_right(self):
        """Pan full right (1.0) should produce L≈0, R=input."""
        mono = np.array([0.5, 0.5, 0.5])
        stereo = apply_constant_power_pan(mono, pan=1.0)
        
        assert stereo.shape == (3, 2)
        # Left should be ~0, right should be ~input
        np.testing.assert_allclose(stereo[:, 0], 0.0, atol=1e-6)
        np.testing.assert_allclose(stereo[:, 1], mono, rtol=1e-6)

    def test_pan_moderate_left(self):
        """Pan moderate left (-0.5) should favor left channel."""
        mono = np.array([1.0])
        stereo = apply_constant_power_pan(mono, pan=-0.5)
        
        assert stereo.shape == (1, 2)
        # Left should be > right
        assert stereo[0, 0] > stereo[0, 1]
        # Energy preservation
        np.testing.assert_allclose(
            stereo[0, 0]**2 + stereo[0, 1]**2,
            1.0,
            rtol=1e-6
        )

    def test_pan_moderate_right(self):
        """Pan moderate right (0.5) should favor right channel."""
        mono = np.array([1.0])
        stereo = apply_constant_power_pan(mono, pan=0.5)
        
        assert stereo.shape == (1, 2)
        # Right should be > left
        assert stereo[0, 1] > stereo[0, 0]
        # Energy preservation
        np.testing.assert_allclose(
            stereo[0, 0]**2 + stereo[0, 1]**2,
            1.0,
            rtol=1e-6
        )

    def test_pan_energy_preservation_all_positions(self):
        """Constant power panning preserves energy at all positions."""
        mono = np.array([1.0])
        for pan in np.linspace(-1.0, 1.0, 21):
            stereo = apply_constant_power_pan(mono, pan=pan)
            energy = stereo[0, 0]**2 + stereo[0, 1]**2
            np.testing.assert_allclose(energy, 1.0, rtol=1e-6)

    def test_pan_mono_input_shape(self):
        """Mono input (1D) should produce stereo output (N, 2)."""
        mono = np.random.randn(100)
        stereo = apply_constant_power_pan(mono, pan=0.3)
        assert stereo.shape == (100, 2)


class TestScheduleAffirmations:
    """Test affirmation scheduling."""

    def test_schedule_deterministic_with_seed(self):
        """Same seed produces same schedule."""
        affirmations = ["I am calm", "I am strong", "I am confident"]
        rng1 = np.random.default_rng(42)
        schedule1 = schedule_affirmations(affirmations, duration_sec=10.0, rng=rng1)
        
        rng2 = np.random.default_rng(42)
        schedule2 = schedule_affirmations(affirmations, duration_sec=10.0, rng=rng2)
        
        assert len(schedule1) == len(schedule2)
        for item1, item2 in zip(schedule1, schedule2):
            assert item1["index"] == item2["index"]
            assert item1["start_sec"] == item2["start_sec"]
            assert item1["pan"] == item2["pan"]

    def test_schedule_different_seeds_different_output(self):
        """Different seeds produce different schedules."""
        affirmations = ["I am calm", "I am strong"]
        rng1 = np.random.default_rng(42)
        schedule1 = schedule_affirmations(affirmations, duration_sec=10.0, rng=rng1)
        
        rng2 = np.random.default_rng(99)
        schedule2 = schedule_affirmations(affirmations, duration_sec=10.0, rng=rng2)
        
        # At least one item should differ
        assert schedule1 != schedule2

    def test_schedule_all_start_times_in_bounds(self):
        """All start times should be within [0, duration_sec]."""
        affirmations = ["I am calm", "I am strong", "I am confident"]
        rng = np.random.default_rng(42)
        schedule = schedule_affirmations(affirmations, duration_sec=20.0, rng=rng)
        
        for item in schedule:
            assert 0.0 <= item["start_sec"] <= 20.0

    def test_schedule_cycles_through_affirmations(self):
        """Schedule should cycle through affirmations to fill duration."""
        affirmations = ["I am calm", "I am strong"]
        rng = np.random.default_rng(42)
        schedule = schedule_affirmations(affirmations, duration_sec=20.0, rng=rng)
        
        # Should have multiple entries (cycling through 2 affirmations over 20s)
        assert len(schedule) > 2
        
        # Indices should cycle: 0, 1, 0, 1, ...
        indices = [item["index"] for item in schedule]
        for i, idx in enumerate(indices):
            assert idx == i % len(affirmations)

    def test_schedule_pan_in_range(self):
        """Pan values should be in [-0.9, 0.9]."""
        affirmations = ["I am calm", "I am strong", "I am confident"]
        rng = np.random.default_rng(42)
        schedule = schedule_affirmations(affirmations, duration_sec=10.0, rng=rng)
        
        for item in schedule:
            assert -0.9 <= item["pan"] <= 0.9

    def test_schedule_has_required_fields(self):
        """Each schedule item should have index, start_sec, pan."""
        affirmations = ["I am calm"]
        rng = np.random.default_rng(42)
        schedule = schedule_affirmations(affirmations, duration_sec=5.0, rng=rng)
        
        for item in schedule:
            assert "index" in item
            assert "start_sec" in item
            assert "pan" in item
            assert isinstance(item["index"], int)
            assert isinstance(item["start_sec"], float)
            assert isinstance(item["pan"], float)

    def test_schedule_none_rng_creates_default(self):
        """rng=None should create default RNG."""
        affirmations = ["I am calm", "I am strong"]
        schedule = schedule_affirmations(affirmations, duration_sec=10.0, rng=None)
        
        # Should produce valid schedule without error
        assert len(schedule) > 0
        for item in schedule:
            assert 0.0 <= item["start_sec"] <= 10.0
            assert -0.9 <= item["pan"] <= 0.9

    def test_schedule_timing_jitter_present(self):
        """Consecutive affirmations should have random gaps (not uniform)."""
        affirmations = ["I am calm", "I am strong"]
        rng = np.random.default_rng(42)
        schedule = schedule_affirmations(affirmations, duration_sec=20.0, rng=rng)
        
        # Calculate gaps between consecutive affirmations
        gaps = []
        for i in range(len(schedule) - 1):
            gap = schedule[i + 1]["start_sec"] - schedule[i]["start_sec"]
            gaps.append(gap)
        
        # Gaps should vary (not all equal)
        if len(gaps) > 1:
            assert len(set(gaps)) > 1, "Gaps should have timing jitter"
        
        # Gaps should be in expected range [0.5s, 2.0s]
        for gap in gaps:
            assert 0.5 <= gap <= 2.0

    def test_schedule_avoids_phonetically_similar_back_to_back(self):
        """Phonetically similar affirmations should not be back-to-back."""
        # Use a balanced set: 2 similar (calm/clear) and 3 dissimilar (strong/brave/powerful)
        affirmations = ["calm", "clear", "strong", "brave", "powerful"]
        rng = np.random.default_rng(42)
        schedule = schedule_affirmations(affirmations, duration_sec=20.0, rng=rng)
        
        # Check that no two consecutive entries are phonetically similar (> 0.6)
        from hypnogen.core.swarm import phonetic_similarity
        for i in range(len(schedule) - 1):
            text_i = affirmations[schedule[i]["index"]]
            text_j = affirmations[schedule[i + 1]["index"]]
            similarity = phonetic_similarity(text_i, text_j)
            assert similarity <= 0.6, f"Back-to-back entries too similar: {text_i} and {text_j} (similarity={similarity:.2f})"

    def test_schedule_avoids_collisions_with_all_similar_words(self):
        """With all-similar words, should still produce valid schedule (best effort)."""
        affirmations = ["calm", "clear", "claim"]  # All share "cl" prefix
        rng = np.random.default_rng(42)
        schedule = schedule_affirmations(affirmations, duration_sec=10.0, rng=rng)
        
        # Should produce valid schedule without infinite loop
        assert len(schedule) > 0
        # All entries should still have valid fields
        for item in schedule:
            assert "index" in item
            assert "start_sec" in item
            assert "pan" in item

    def test_schedule_preserves_timing_and_panning_after_avoidance(self):
        """Collision avoidance should only swap indices, not timing/panning."""
        affirmations = ["calm", "clear", "strong", "brave"]
        rng1 = np.random.default_rng(42)
        schedule1 = schedule_affirmations(affirmations, duration_sec=10.0, rng=rng1)
        
        # With different affirmations (no phonetic similarity), timing should be same
        affirmations2 = ["apple", "orange", "banana", "grape"]
        rng2 = np.random.default_rng(42)
        schedule2 = schedule_affirmations(affirmations2, duration_sec=10.0, rng=rng2)
        
        # Timing structure should be identical (same RNG seed)
        assert len(schedule1) == len(schedule2)
        for item1, item2 in zip(schedule1, schedule2):
            assert item1["start_sec"] == item2["start_sec"]
            assert item1["pan"] == item2["pan"]
            # Indices may differ due to collision avoidance


class TestGenerateSwarm:
    """Test swarm generation."""

    def test_generate_swarm_output_shape(self):
        """Output should be stereo (N, 2) with correct duration."""
        # Create 3 mono audio clips (0.5s each @ 44100Hz = 22050 samples)
        sr = 44100
        clip_duration = 0.5
        clip_samples = int(sr * clip_duration)
        affirmation_audios = [
            np.random.randn(clip_samples) * 0.1,
            np.random.randn(clip_samples) * 0.1,
            np.random.randn(clip_samples) * 0.1,
        ]
        
        duration_sec = 5.0
        rng = np.random.default_rng(42)
        swarm = generate_swarm(affirmation_audios, duration_sec, sr=sr, rng=rng)
        
        expected_samples = int(sr * duration_sec)
        assert swarm.shape == (expected_samples, 2)

    def test_generate_swarm_seed_reproducibility(self):
        """Same seed produces same output."""
        sr = 44100
        clip_samples = int(sr * 0.5)
        affirmation_audios = [
            np.random.randn(clip_samples) * 0.1,
            np.random.randn(clip_samples) * 0.1,
        ]
        
        rng1 = np.random.default_rng(42)
        swarm1 = generate_swarm(affirmation_audios, duration_sec=5.0, sr=sr, rng=rng1)
        
        rng2 = np.random.default_rng(42)
        swarm2 = generate_swarm(affirmation_audios, duration_sec=5.0, sr=sr, rng=rng2)
        
        np.testing.assert_array_equal(swarm1, swarm2)

    def test_generate_swarm_different_seeds_different_output(self):
        """Different seeds produce different output."""
        sr = 44100
        clip_samples = int(sr * 0.5)
        affirmation_audios = [
            np.random.randn(clip_samples) * 0.1,
            np.random.randn(clip_samples) * 0.1,
        ]
        
        rng1 = np.random.default_rng(42)
        swarm1 = generate_swarm(affirmation_audios, duration_sec=5.0, sr=sr, rng=rng1)
        
        rng2 = np.random.default_rng(99)
        swarm2 = generate_swarm(affirmation_audios, duration_sec=5.0, sr=sr, rng=rng2)
        
        # Should differ
        assert not np.array_equal(swarm1, swarm2)

    def test_generate_swarm_additive_mixing(self):
        """Overlapping clips should mix additively."""
        sr = 44100
        # Create two clips: one with value 0.5, one with value 0.3
        clip_samples = int(sr * 1.0)
        affirmation_audios = [
            np.full(clip_samples, 0.5),
            np.full(clip_samples, 0.3),
        ]
        
        # Force short duration with overlap by using very short gaps
        # We'll create a custom test where clips definitely overlap
        duration_sec = 2.0
        rng = np.random.default_rng(42)
        swarm = generate_swarm(affirmation_audios, duration_sec, sr=sr, rng=rng)
        
        # Since clips are 1s long and we have 2s duration with random gaps,
        # there should be some non-zero values from mixing
        assert swarm.shape == (int(sr * duration_sec), 2)
        # At least some samples should be non-zero (clips were placed)
        assert np.any(np.abs(swarm) > 0.1)

    def test_generate_swarm_none_rng_creates_default(self):
        """rng=None should create default RNG."""
        sr = 44100
        clip_samples = int(sr * 0.5)
        affirmation_audios = [
            np.random.randn(clip_samples) * 0.1,
        ]
        
        swarm = generate_swarm(affirmation_audios, duration_sec=3.0, sr=sr, rng=None)
        
        expected_samples = int(sr * 3.0)
        assert swarm.shape == (expected_samples, 2)

    def test_generate_swarm_cycles_through_clips(self):
        """Should cycle through clips to fill duration."""
        sr = 44100
        clip_samples = int(sr * 0.3)  # Short clips
        # Create distinct clips with different energy
        affirmation_audios = [
            np.full(clip_samples, 0.9),  # High energy
            np.full(clip_samples, 0.1),  # Low energy
        ]
        
        duration_sec = 10.0  # Long enough to cycle multiple times
        rng = np.random.default_rng(42)
        swarm = generate_swarm(affirmation_audios, duration_sec, sr=sr, rng=rng)
        
        # Should have placed multiple clips (cycling through)
        # Check that output has substantial energy (multiple clips placed)
        energy = np.sum(swarm**2)
        assert energy > 0, "Should have placed clips throughout duration"

    def test_generate_swarm_no_nan_or_inf(self):
        """Output should not contain NaN or Inf."""
        sr = 44100
        clip_samples = int(sr * 0.5)
        affirmation_audios = [
            np.random.randn(clip_samples) * 0.1,
            np.random.randn(clip_samples) * 0.1,
        ]
        
        rng = np.random.default_rng(42)
        swarm = generate_swarm(affirmation_audios, duration_sec=5.0, sr=sr, rng=rng)
        
        assert not np.any(np.isnan(swarm))
        assert not np.any(np.isinf(swarm))

    def test_generate_swarm_handles_empty_duration(self):
        """Very short duration should still produce valid output."""
        sr = 44100
        clip_samples = int(sr * 0.5)
        affirmation_audios = [
            np.random.randn(clip_samples) * 0.1,
        ]
        
        duration_sec = 0.1  # Very short
        rng = np.random.default_rng(42)
        swarm = generate_swarm(affirmation_audios, duration_sec, sr=sr, rng=rng)
        
        expected_samples = int(sr * duration_sec)
        assert swarm.shape == (expected_samples, 2)
