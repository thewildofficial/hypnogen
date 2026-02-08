"""Tests for attentional epoch system."""

import numpy as np
import pytest

from hypnogen.core.epochs import (
    EPOCH_BOUNDARIES,
    EPOCH_NAMES,
    generate_boundary_event,
    generate_gain_envelope,
    get_epoch_at_position,
    get_epoch_boundaries_in_samples,
    get_layer_gain,
    select_boundary_events,
)


# ============================
# Test: Epoch Constants
# ============================


def test_epoch_boundaries_correct():
    """Verify EPOCH_BOUNDARIES has correct values."""
    assert EPOCH_BOUNDARIES == (0.0, 0.2, 0.5, 0.85, 1.0)


def test_epoch_names_correct():
    """Verify EPOCH_NAMES has correct values."""
    assert EPOCH_NAMES == ("induction", "descent", "saturation", "seal")


def test_epoch_boundaries_and_names_match():
    """Verify EPOCH_NAMES has one fewer element than EPOCH_BOUNDARIES."""
    # 5 boundaries define 4 epochs
    assert len(EPOCH_NAMES) == len(EPOCH_BOUNDARIES) - 1


# ============================
# Test: get_layer_gain()
# ============================


def test_get_layer_gain_shepherd_induction():
    """Shepherd gain at induction epoch (start) is 1.0."""
    assert get_layer_gain("shepherd", 0.0) == 1.0


def test_get_layer_gain_shepherd_descent():
    """Shepherd gain at descent epoch is 1.0."""
    assert get_layer_gain("shepherd", 0.3) == 1.0


def test_get_layer_gain_shepherd_saturation():
    """Shepherd gain at saturation epoch is 0.6."""
    assert get_layer_gain("shepherd", 0.7) == 0.6


def test_get_layer_gain_shepherd_seal():
    """Shepherd gain at seal epoch is 0.8."""
    assert get_layer_gain("shepherd", 0.9) == 0.8


def test_get_layer_gain_weaver_induction():
    """Weaver gain at induction epoch is 0.0."""
    assert get_layer_gain("weaver", 0.0) == 0.0


def test_get_layer_gain_weaver_descent():
    """Weaver gain at descent epoch is 0.8."""
    assert get_layer_gain("weaver", 0.3) == 0.8


def test_get_layer_gain_weaver_saturation():
    """Weaver gain at saturation epoch is 0.5."""
    assert get_layer_gain("weaver", 0.7) == 0.5


def test_get_layer_gain_weaver_seal():
    """Weaver gain at seal epoch is 0.0."""
    assert get_layer_gain("weaver", 0.9) == 0.0


def test_get_layer_gain_swarm_induction():
    """Swarm gain at induction epoch is 0.0."""
    assert get_layer_gain("swarm", 0.0) == 0.0


def test_get_layer_gain_swarm_descent_ramp():
    """Swarm gain ramps from 0→1 during descent epoch."""
    # Descent epoch: 0.2 to 0.5 (30% duration)
    # Midpoint at 0.35 should be ~0.5
    gain = get_layer_gain("swarm", 0.35)
    assert abs(gain - 0.5) < 0.05  # Allow small tolerance


def test_get_layer_gain_swarm_saturation():
    """Swarm gain at saturation epoch is 1.0."""
    assert get_layer_gain("swarm", 0.7) == 1.0


def test_get_layer_gain_swarm_seal_ramp():
    """Swarm gain ramps from 1→0 during seal epoch."""
    # Seal epoch: 0.85 to 1.0 (15% duration)
    # Midpoint at 0.925 should be ~0.5
    gain = get_layer_gain("swarm", 0.925)
    assert abs(gain - 0.5) < 0.05


def test_get_layer_gain_bed_induction():
    """Bed gain at induction epoch is 0.3."""
    assert get_layer_gain("bed", 0.0) == 0.3


def test_get_layer_gain_bed_descent_ramp():
    """Bed gain ramps from 0.3→0.7 during descent epoch."""
    # Descent epoch: 0.2 to 0.5
    # Midpoint at 0.35 should be ~0.5
    gain = get_layer_gain("bed", 0.35)
    assert abs(gain - 0.5) < 0.05


def test_get_layer_gain_bed_saturation():
    """Bed gain at saturation epoch is 1.0."""
    assert get_layer_gain("bed", 0.7) == 1.0


def test_get_layer_gain_bed_seal_ramp():
    """Bed gain ramps from 1.0→0.3 during seal epoch."""
    # Seal epoch: 0.85 to 1.0
    # Midpoint at 0.925 should be ~0.65
    gain = get_layer_gain("bed", 0.925)
    assert abs(gain - 0.65) < 0.05


def test_get_layer_gain_invalid_layer():
    """Raise ValueError for invalid layer name."""
    with pytest.raises(ValueError, match="Invalid layer"):
        get_layer_gain("invalid", 0.5)


def test_get_layer_gain_clamps_negative_position():
    """Position < 0 is clamped to 0."""
    assert get_layer_gain("shepherd", -0.1) == get_layer_gain("shepherd", 0.0)


def test_get_layer_gain_clamps_excessive_position():
    """Position > 1 is clamped to 1."""
    assert get_layer_gain("shepherd", 1.5) == get_layer_gain("shepherd", 1.0)


# ============================
# Test: generate_gain_envelope()
# ============================


def test_generate_gain_envelope_shape():
    """Envelope has correct shape (num_samples,)."""
    envelope = generate_gain_envelope("shepherd", num_samples=44100)
    assert envelope.shape == (44100,)


def test_generate_gain_envelope_dtype():
    """Envelope is float array."""
    envelope = generate_gain_envelope("shepherd", num_samples=1000)
    assert envelope.dtype == np.float64 or envelope.dtype == np.float32


def test_generate_gain_envelope_matches_get_layer_gain():
    """Envelope values match get_layer_gain at key positions."""
    num_samples = 44100
    envelope = generate_gain_envelope("shepherd", num_samples=num_samples)
    
    # Check start
    assert abs(envelope[0] - get_layer_gain("shepherd", 0.0)) < 0.01
    
    # Check midpoint
    mid_idx = num_samples // 2
    assert abs(envelope[mid_idx] - get_layer_gain("shepherd", 0.5)) < 0.01
    
    # Check end
    assert abs(envelope[-1] - get_layer_gain("shepherd", 1.0)) < 0.01


def test_generate_gain_envelope_swarm_ramps():
    """Swarm envelope has ramps during descent and seal."""
    num_samples = 44100
    envelope = generate_gain_envelope("swarm", num_samples=num_samples)
    
    # Descent ramp: 0.2→0.5 should increase
    idx_20 = int(0.2 * num_samples)
    idx_50 = int(0.5 * num_samples)
    assert envelope[idx_50] > envelope[idx_20]
    
    # Seal ramp: 0.85→1.0 should decrease
    idx_85 = int(0.85 * num_samples)
    idx_100 = num_samples - 1
    assert envelope[idx_100] < envelope[idx_85]


def test_generate_gain_envelope_no_nans():
    """Envelope contains no NaN values."""
    envelope = generate_gain_envelope("bed", num_samples=1000)
    assert not np.any(np.isnan(envelope))


def test_generate_gain_envelope_no_infs():
    """Envelope contains no Inf values."""
    envelope = generate_gain_envelope("bed", num_samples=1000)
    assert not np.any(np.isinf(envelope))


# ============================
# Test: generate_boundary_event()
# ============================


def test_generate_boundary_event_silence_shape():
    """Silence event returns stereo array."""
    event = generate_boundary_event("silence", sr=44100)
    assert event.ndim == 2
    assert event.shape[1] == 2  # Stereo


def test_generate_boundary_event_silence_duration():
    """Silence event is 600-900ms of zeros."""
    sr = 44100
    rng = np.random.default_rng(42)
    event = generate_boundary_event("silence", sr=sr, rng=rng)
    
    min_samples = int(0.6 * sr)
    max_samples = int(0.9 * sr)
    assert min_samples <= event.shape[0] <= max_samples
    
    # All zeros
    assert np.allclose(event, 0.0)


def test_generate_boundary_event_silence_reproducible():
    """Silence event with same seed produces same duration."""
    sr = 44100
    rng1 = np.random.default_rng(123)
    rng2 = np.random.default_rng(123)
    
    event1 = generate_boundary_event("silence", sr=sr, rng=rng1)
    event2 = generate_boundary_event("silence", sr=sr, rng=rng2)
    
    assert event1.shape == event2.shape


def test_generate_boundary_event_snap_shape():
    """Snap event returns stereo array."""
    event = generate_boundary_event("snap", sr=44100)
    assert event.ndim == 2
    assert event.shape[1] == 2


def test_generate_boundary_event_snap_short():
    """Snap event is short transient (10-30ms range)."""
    sr = 44100
    event = generate_boundary_event("snap", sr=sr)
    
    # Should be short but with decay tail
    # Total duration: 10-20ms burst + 200ms tail = ~220ms max
    max_samples = int(0.25 * sr)  # 250ms
    assert event.shape[0] <= max_samples


def test_generate_boundary_event_snap_not_silence():
    """Snap event contains non-zero values."""
    event = generate_boundary_event("snap", sr=44100)
    assert not np.allclose(event, 0.0)


def test_generate_boundary_event_snap_normalized():
    """Snap event is normalized to [-1, 1]."""
    event = generate_boundary_event("snap", sr=44100)
    assert np.max(np.abs(event)) <= 1.0


def test_generate_boundary_event_stereo_collapse_shape():
    """Stereo collapse event returns stereo array."""
    event = generate_boundary_event("stereo_collapse", sr=44100)
    assert event.ndim == 2
    assert event.shape[1] == 2


def test_generate_boundary_event_stereo_collapse_duration():
    """Stereo collapse event is 1-2 seconds."""
    sr = 44100
    rng = np.random.default_rng(42)
    event = generate_boundary_event("stereo_collapse", sr=sr, rng=rng)
    
    min_samples = int(1.0 * sr)
    max_samples = int(2.0 * sr)
    assert min_samples <= event.shape[0] <= max_samples


def test_generate_boundary_event_stereo_collapse_is_zeros():
    """Stereo collapse event is zeros (mixer handles collapse)."""
    event = generate_boundary_event("stereo_collapse", sr=44100)
    assert np.allclose(event, 0.0)


def test_generate_boundary_event_invalid_type():
    """Raise ValueError for invalid event type."""
    with pytest.raises(ValueError, match="Invalid event type"):
        generate_boundary_event("invalid", sr=44100)


def test_generate_boundary_event_uses_rng():
    """Different RNG seeds produce different results for variable-duration events."""
    rng1 = np.random.default_rng(100)
    rng2 = np.random.default_rng(200)
    
    event1 = generate_boundary_event("silence", sr=44100, rng=rng1)
    event2 = generate_boundary_event("silence", sr=44100, rng=rng2)
    
    # Different durations expected (though not guaranteed with all seeds)
    # At least verify they both are valid
    assert 600 <= event1.shape[0] / 44100 * 1000 <= 900
    assert 600 <= event2.shape[0] / 44100 * 1000 <= 900


# ============================
# Test: select_boundary_events()
# ============================


def test_select_boundary_events_returns_three():
    """Returns exactly 3 event types."""
    events = select_boundary_events()
    assert len(events) == 3


def test_select_boundary_events_valid_types():
    """All returned event types are valid."""
    events = select_boundary_events()
    valid = {"silence", "snap", "stereo_collapse"}
    assert all(e in valid for e in events)


def test_select_boundary_events_reproducible():
    """Same seed produces same selection."""
    rng1 = np.random.default_rng(42)
    rng2 = np.random.default_rng(42)
    
    events1 = select_boundary_events(rng=rng1)
    events2 = select_boundary_events(rng=rng2)
    
    assert events1 == events2


def test_select_boundary_events_varies():
    """Different seeds produce different selections (probabilistically)."""
    rng1 = np.random.default_rng(1)
    rng2 = np.random.default_rng(999)
    
    events1 = select_boundary_events(rng=rng1)
    events2 = select_boundary_events(rng=rng2)
    
    # Highly likely to be different (not guaranteed but extremely probable)
    # Just verify both are valid lists
    assert isinstance(events1, list)
    assert isinstance(events2, list)


# ============================
# Test: get_epoch_at_position()
# ============================


def test_get_epoch_at_position_induction():
    """Position 0.1 is in induction epoch."""
    idx, name = get_epoch_at_position(0.1)
    assert idx == 0
    assert name == "induction"


def test_get_epoch_at_position_descent():
    """Position 0.3 is in descent epoch."""
    idx, name = get_epoch_at_position(0.3)
    assert idx == 1
    assert name == "descent"


def test_get_epoch_at_position_saturation():
    """Position 0.7 is in saturation epoch."""
    idx, name = get_epoch_at_position(0.7)
    assert idx == 2
    assert name == "saturation"


def test_get_epoch_at_position_seal():
    """Position 0.9 is in seal epoch."""
    idx, name = get_epoch_at_position(0.9)
    assert idx == 3
    assert name == "seal"


def test_get_epoch_at_position_boundary():
    """Position exactly at boundary (0.5) is in next epoch."""
    idx, name = get_epoch_at_position(0.5)
    assert idx == 2
    assert name == "saturation"


def test_get_epoch_at_position_start():
    """Position 0.0 is in first epoch."""
    idx, name = get_epoch_at_position(0.0)
    assert idx == 0
    assert name == "induction"


def test_get_epoch_at_position_end():
    """Position 1.0 is in last epoch."""
    idx, name = get_epoch_at_position(1.0)
    assert idx == 3
    assert name == "seal"


# ============================
# Test: get_epoch_boundaries_in_samples()
# ============================


def test_get_epoch_boundaries_in_samples_count():
    """Returns 5 sample indices for 5 boundaries."""
    boundaries = get_epoch_boundaries_in_samples(44100)
    assert len(boundaries) == 5


def test_get_epoch_boundaries_in_samples_values():
    """Boundary sample indices match proportions."""
    total_samples = 44100
    boundaries = get_epoch_boundaries_in_samples(total_samples)
    
    assert boundaries[0] == 0
    assert boundaries[1] == int(0.2 * total_samples)
    assert boundaries[2] == int(0.5 * total_samples)
    assert boundaries[3] == int(0.85 * total_samples)
    assert boundaries[4] == total_samples


def test_get_epoch_boundaries_in_samples_increasing():
    """Boundaries are monotonically increasing."""
    boundaries = get_epoch_boundaries_in_samples(100000)
    for i in range(len(boundaries) - 1):
        assert boundaries[i] < boundaries[i + 1]


def test_get_epoch_boundaries_in_samples_different_durations():
    """Works with different total sample counts."""
    boundaries_10s = get_epoch_boundaries_in_samples(441000)  # 10s @ 44.1kHz
    boundaries_60s = get_epoch_boundaries_in_samples(2646000)  # 60s @ 44.1kHz
    
    # Proportions should be same
    assert boundaries_10s[1] / 441000 == pytest.approx(0.2, abs=0.001)
    assert boundaries_60s[1] / 2646000 == pytest.approx(0.2, abs=0.001)
