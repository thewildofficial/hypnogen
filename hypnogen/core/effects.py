"""Audio effects module for post-processing segments.

Provides pitch shifting, time stretching, and crossfading for analog marking
of embedded commands.
"""

import numpy as np
import librosa


def apply_pitch_shift(audio: np.ndarray, sr: int, n_steps: float) -> np.ndarray:
    """Apply pitch shift to audio without changing duration.

    Args:
        audio: Mono audio signal as 1D numpy array
        sr: Sample rate in Hz
        n_steps: Number of semitones to shift (positive = higher, negative = lower)

    Returns:
        Pitch-shifted audio as 1D numpy array (same length as input)
    """
    if n_steps == 0.0:
        return audio.copy()

    # Use n_fft=1024 for ~13x faster STFT (vs default 2048).
    # Quality difference is inaudible for speech pitch shifts of 1-3 semitones.
    shifted = librosa.effects.pitch_shift(y=audio, sr=sr, n_steps=n_steps, n_fft=1024)
    return shifted


def apply_time_stretch(audio: np.ndarray, rate: float) -> np.ndarray:
    """Apply time stretching to audio.

    Args:
        audio: Mono audio signal as 1D numpy array
        rate: Time stretch factor (rate > 1.0 = faster/shorter, rate < 1.0 = slower/longer)

    Returns:
        Time-stretched audio as 1D numpy array (length changes proportionally)
    """
    if rate == 1.0:
        return audio.copy()

    # Use n_fft=1024 for ~13x faster STFT (vs default 2048).
    # Quality difference is inaudible for speech time stretches of 0.8-1.2x.
    stretched = librosa.effects.time_stretch(y=audio, rate=rate, n_fft=1024)
    return stretched


def crossfade(
    audio_a: np.ndarray,
    audio_b: np.ndarray,
    crossfade_ms: int = 50,
    sr: int = 44100
) -> np.ndarray:
    """Join two audio segments with equal-power crossfade.

    Args:
        audio_a: First audio segment (mono 1D array)
        audio_b: Second audio segment (mono 1D array)
        crossfade_ms: Crossfade duration in milliseconds (default: 50ms)
        sr: Sample rate in Hz (default: 44100)

    Returns:
        Crossfaded audio as 1D numpy array
        Length = len(audio_a) + len(audio_b) - crossfade_samples
    """
    if crossfade_ms == 0:
        return np.concatenate([audio_a, audio_b])

    crossfade_samples = int(crossfade_ms * sr / 1000)

    # Ensure crossfade region doesn't exceed segment lengths
    crossfade_samples = min(crossfade_samples, len(audio_a), len(audio_b))

    if crossfade_samples == 0:
        return np.concatenate([audio_a, audio_b])

    # Extract regions
    a_before = audio_a[:-crossfade_samples]
    a_overlap = audio_a[-crossfade_samples:]
    b_overlap = audio_b[:crossfade_samples]
    b_after = audio_b[crossfade_samples:]

    # Equal-power crossfade curves (sqrt for energy preservation)
    fade_out = np.sqrt(np.linspace(1, 0, crossfade_samples))
    fade_in = np.sqrt(np.linspace(0, 1, crossfade_samples))

    # Apply crossfade
    crossfaded_region = a_overlap * fade_out + b_overlap * fade_in

    # Combine all parts
    result = np.concatenate([a_before, crossfaded_region, b_after])
    return result


def apply_analog_marking(
    audio: np.ndarray,
    sr: int,
    pitch_shift: float = 0.0,
    rate: float = 1.0
) -> np.ndarray:
    """Apply analog marking effects to audio segment.

    Convenience wrapper that applies both pitch shift and time stretch
    for marking embedded commands. Pitch shift is applied first, then
    time stretch.

    Typical values for embedded commands:
    - pitch_shift: -2.0 to -3.0 semitones (deeper voice)
    - rate: 0.85 to 0.95 (slightly slower)

    Args:
        audio: Mono audio signal as 1D numpy array
        sr: Sample rate in Hz
        pitch_shift: Number of semitones to shift (default: 0.0 = no shift)
        rate: Time stretch factor (default: 1.0 = no stretch)

    Returns:
        Processed audio as 1D numpy array
    """
    # Apply pitch shift first (preserves duration)
    result = apply_pitch_shift(audio, sr, pitch_shift)

    # Then apply time stretch (changes duration)
    result = apply_time_stretch(result, rate)

    return result
