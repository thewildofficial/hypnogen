"""Multi-track mixer with epoch-aware gain staging.

Handles layer summation, per-layer gain staging with epoch-based gain envelopes,
epoch boundary event insertion, and peak limiting. Does NOT handle file I/O.
"""

import numpy as np
from pedalboard import Limiter

from hypnogen.core.epochs import (
    EPOCH_BOUNDARIES,
    generate_boundary_event,
    generate_gain_envelope,
    select_boundary_events,
)

# Default per-layer gain values in dB
DEFAULT_GAIN_DB: dict[str, float] = {
    "shepherd": -6.0,
    "weaver": -8.0,
    "swarm": -18.0,
    "bed": -12.0,
}

# Layer names in processing order
LAYER_NAMES = ("shepherd", "weaver", "swarm", "bed")


def apply_gain_db(audio: np.ndarray, gain_db: float) -> np.ndarray:
    """Apply gain in dB to audio array.

    Args:
        audio: Audio array (any shape)
        gain_db: Gain in dB (positive = amplify, negative = attenuate)

    Returns:
        Audio array with gain applied
    """
    gain_linear = 10 ** (gain_db / 20)
    return audio * gain_linear


def apply_limiter(
    audio: np.ndarray,
    sr: int,
    threshold_db: float = -1.0,
    release_ms: float = 100.0,
) -> np.ndarray:
    """Apply peak limiter to audio using pedalboard.

    Args:
        audio: Audio array, mono (N,) or stereo (N, 2)
        sr: Sample rate
        threshold_db: Limiting threshold in dB (default -1.0 dBFS)
        release_ms: Release time in milliseconds

    Returns:
        Limited audio array with same shape as input
    """
    # Handle empty or minimal audio
    if audio.size == 0:
        return audio

    # Track original shape and dtype
    original_shape = audio.shape
    original_ndim = audio.ndim
    original_dtype = audio.dtype
    original_length = audio.shape[0]

    # Convert to float32 for pedalboard
    audio_f32 = audio.astype(np.float32)

    # Pedalboard expects (channels, samples) and fails on square arrays (e.g., (2,2))
    if original_ndim == 1:
        audio_f32 = audio_f32.reshape(1, -1)
        num_channels = 1
    elif original_ndim == 2:
        audio_f32 = audio_f32.T
        num_channels = 2
    else:
        num_channels = 1

    min_samples = num_channels + 1
    padded = False
    if audio_f32.shape[1] <= num_channels:
        padding = np.zeros((num_channels, min_samples - audio_f32.shape[1]), dtype=np.float32)
        audio_f32 = np.concatenate([audio_f32, padding], axis=1)
        padded = True

    limiter = Limiter(threshold_db=threshold_db, release_ms=release_ms)
    limited = limiter(audio_f32, sr)

    if padded:
        limited = limited[:, :original_length]

    if original_ndim == 1:
        limited = limited.reshape(-1)
    elif original_ndim == 2:
        limited = limited.T

    if original_dtype != np.float32:
        limited = limited.astype(original_dtype)

    return limited


def mix_layers(
    shepherd: np.ndarray | None = None,
    weaver: np.ndarray | None = None,
    swarm: np.ndarray | None = None,
    bed: np.ndarray | None = None,
    sr: int = 44100,
    gain_db: dict[str, float] | None = None,
    apply_epochs: bool = True,
    boundary_events: list[str] | None = None,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Mix multiple audio layers with epoch-aware gain staging.

    Args:
        shepherd: Shepherd layer (N, 2) stereo or None
        weaver: Weaver layer (N, 2) stereo or None
        swarm: Swarm layer (N, 2) stereo or None
        bed: Bed layer (N, 2) stereo or None
        sr: Sample rate
        gain_db: Per-layer dB gains, overrides defaults
        apply_epochs: Whether to apply epoch gain envelopes
        boundary_events: List of 3 event types for epoch boundaries
        rng: Random number generator for boundary events

    Returns:
        Stereo audio array (N, 2), peak-limited to avoid clipping
    """
    if rng is None:
        rng = np.random.default_rng()

    # Merge gains with defaults
    gains = DEFAULT_GAIN_DB.copy()
    if gain_db is not None:
        gains.update(gain_db)

    # Build layer dict
    layers = {
        "shepherd": shepherd,
        "weaver": weaver,
        "swarm": swarm,
        "bed": bed,
    }

    # Filter out None layers
    active_layers = {name: arr for name, arr in layers.items() if arr is not None}

    # Handle case where all layers are None
    if not active_layers:
        # Return minimal stereo silence
        return np.zeros((1, 2), dtype=np.float32)

    # Determine target length (max of all layer lengths)
    target_length = max(arr.shape[0] for arr in active_layers.values())

    # Process each layer: pad, apply static gain, apply epoch envelope
    processed_layers = []

    for name in LAYER_NAMES:
        layer = active_layers.get(name)
        if layer is None:
            continue

        # Pad to target length if needed
        if layer.shape[0] < target_length:
            padding = np.zeros((target_length - layer.shape[0], 2), dtype=layer.dtype)
            layer = np.concatenate([layer, padding], axis=0)

        # Apply static gain (dB)
        layer = apply_gain_db(layer, gains[name])

        # Apply epoch gain envelope if enabled
        if apply_epochs:
            envelope = generate_gain_envelope(name, target_length)
            # Expand envelope to match stereo shape: (N,) -> (N, 1)
            layer = layer * envelope[:, np.newaxis]

        processed_layers.append(layer)

    # Sum all layers
    mixed = np.zeros((target_length, 2), dtype=np.float64)
    for layer in processed_layers:
        mixed += layer

    # Convert to float32
    mixed = mixed.astype(np.float32)

    # Insert epoch boundary events at transition points
    if boundary_events is not None:
        mixed = _insert_boundary_events(mixed, sr, boundary_events, rng)

    # Apply peak limiter
    mixed = apply_limiter(mixed, sr, threshold_db=-1.0)

    return mixed


def _insert_boundary_events(
    audio: np.ndarray,
    sr: int,
    event_types: list[str],
    rng: np.random.Generator,
) -> np.ndarray:
    if len(event_types) != 3:
        return audio

    total_samples = audio.shape[0]
    result = audio.copy()

    boundary_positions = [EPOCH_BOUNDARIES[1], EPOCH_BOUNDARIES[2], EPOCH_BOUNDARIES[3]]
    boundary_samples = [int(pos * total_samples) for pos in boundary_positions]

    for sample_pos, event_type in zip(boundary_samples, event_types):
        event = generate_boundary_event(event_type, sr, rng)
        event_samples = event.shape[0]

        end_pos = min(sample_pos + event_samples, total_samples)
        actual_samples = end_pos - sample_pos

        if actual_samples > 0:
            result[sample_pos:end_pos] += event[:actual_samples] * 0.3

    return result
