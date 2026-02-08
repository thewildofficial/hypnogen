"""Attentional epoch system for Hypnogen.

Defines epoch boundaries, per-layer gain envelopes, and boundary event generation.
This is pure math/logic with no I/O.
"""

import numpy as np

# ============================
# Epoch Definitions
# ============================

# Epoch boundaries (normalized to 0.0-1.0 of total duration)
EPOCH_BOUNDARIES = (0.0, 0.2, 0.5, 0.85, 1.0)

# Epoch names (one per interval between boundaries)
EPOCH_NAMES = ("induction", "descent", "saturation", "seal")

# Layer gain profiles per epoch
# Format: {layer: [(start_gain, end_gain), ...]} for each of 4 epochs
# Constant value = (x, x), ramp = (start, end)
_LAYER_GAIN_PROFILES = {
    "shepherd": [(1.0, 1.0), (1.0, 1.0), (0.6, 0.6), (0.8, 0.8)],
    "weaver": [(0.0, 0.0), (0.8, 0.8), (0.5, 0.5), (0.0, 0.0)],
    "swarm": [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)],  # Ramps in descent and seal
    "bed": [(0.3, 0.3), (0.3, 0.7), (1.0, 1.0), (1.0, 0.3)],  # Ramps in descent and seal
}


# ============================
# Gain Envelope Functions
# ============================


def get_layer_gain(layer: str, position: float) -> float:
    """Get gain multiplier for a layer at a normalized position.

    Args:
        layer: One of "shepherd", "weaver", "swarm", "bed"
        position: Normalized time position (0.0 = start, 1.0 = end)

    Returns:
        Gain multiplier (0.0 to 1.0)

    Raises:
        ValueError: If layer name is invalid
    """
    if layer not in _LAYER_GAIN_PROFILES:
        raise ValueError(f"Invalid layer: {layer}")

    position = max(0.0, min(1.0, position))
    profile = _LAYER_GAIN_PROFILES[layer]

    for i in range(len(EPOCH_BOUNDARIES) - 1):
        start_pos = EPOCH_BOUNDARIES[i]
        end_pos = EPOCH_BOUNDARIES[i + 1]

        is_last_epoch = (i == len(EPOCH_BOUNDARIES) - 2)
        if is_last_epoch:
            in_epoch = start_pos <= position <= end_pos
        else:
            in_epoch = start_pos <= position < end_pos

        if in_epoch:
            start_gain, end_gain = profile[i]
            
            if end_pos == start_pos:
                return start_gain

            t = (position - start_pos) / (end_pos - start_pos)
            return start_gain + t * (end_gain - start_gain)

    return profile[-1][1]


def generate_gain_envelope(layer: str, num_samples: int) -> np.ndarray:
    """Generate a gain envelope array for a layer.

    Args:
        layer: One of "shepherd", "weaver", "swarm", "bed"
        num_samples: Total number of audio samples

    Returns:
        1D numpy array of gain multipliers, shape (num_samples,)
    """
    positions = np.linspace(0.0, 1.0, num_samples)
    envelope = np.array([get_layer_gain(layer, pos) for pos in positions])
    return envelope


# ============================
# Boundary Event Generation
# ============================


def generate_boundary_event(
    event_type: str,
    sr: int = 44100,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Generate a single epoch boundary event.

    Args:
        event_type: One of "silence", "snap", "stereo_collapse"
        sr: Sample rate
        rng: Random number generator

    Returns:
        Stereo audio array (N, 2)

    Raises:
        ValueError: If event_type is invalid
    """
    if rng is None:
        rng = np.random.default_rng()

    if event_type == "silence":
        # 600-900ms of zeros
        duration_sec = rng.uniform(0.6, 0.9)
        num_samples = int(sr * duration_sec)
        return np.zeros((num_samples, 2))

    elif event_type == "snap":
        # Short transient burst: 10-20ms noise with fast exponential decay
        burst_duration_ms = rng.uniform(10, 20)
        burst_samples = int(sr * burst_duration_ms / 1000.0)

        # Decay tail: 200ms
        tail_samples = int(sr * 0.2)
        total_samples = burst_samples + tail_samples

        # Generate noise burst
        burst = rng.standard_normal(burst_samples)

        # Create exponential decay envelope
        decay = np.exp(-np.linspace(0, 5, total_samples))

        # Apply decay to burst + silence
        signal = np.concatenate([burst, np.zeros(tail_samples)])
        signal = signal * decay

        # Normalize
        max_val = np.max(np.abs(signal))
        if max_val > 0:
            signal = signal / max_val

        # Convert to stereo
        return np.column_stack([signal, signal])

    elif event_type == "stereo_collapse":
        # 1-2 seconds of zeros (mixer will handle actual collapse)
        duration_sec = rng.uniform(1.0, 2.0)
        num_samples = int(sr * duration_sec)
        return np.zeros((num_samples, 2))

    else:
        raise ValueError(f"Invalid event type: {event_type}")


def select_boundary_events(
    rng: np.random.Generator | None = None,
) -> list[str]:
    """Select one event type for each of the 3 epoch boundaries.

    Args:
        rng: Random number generator

    Returns:
        List of 3 event types, one per boundary
    """
    if rng is None:
        rng = np.random.default_rng()

    event_types = ["silence", "snap", "stereo_collapse"]
    return [rng.choice(event_types) for _ in range(3)]


# ============================
# Helper Functions
# ============================


def get_epoch_at_position(position: float) -> tuple[int, str]:
    """Return (epoch_index, epoch_name) for a normalized position.

    Args:
        position: Normalized time position (0.0 to 1.0)

    Returns:
        Tuple of (epoch_index, epoch_name)
    """
    # Clamp position
    position = max(0.0, min(1.0, position))

    # Find epoch
    for i in range(len(EPOCH_BOUNDARIES) - 1):
        if EPOCH_BOUNDARIES[i] <= position < EPOCH_BOUNDARIES[i + 1]:
            return (i, EPOCH_NAMES[i])

    # If exactly at end, return last epoch
    return (len(EPOCH_NAMES) - 1, EPOCH_NAMES[-1])


def get_epoch_boundaries_in_samples(total_samples: int) -> list[int]:
    """Return sample indices for epoch boundaries.

    Args:
        total_samples: Total number of samples

    Returns:
        List of 5 sample indices (one per boundary)
    """
    return [int(boundary * total_samples) for boundary in EPOCH_BOUNDARIES]
