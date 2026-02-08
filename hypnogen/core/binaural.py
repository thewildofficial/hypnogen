"""Binaural beat and pink noise generation for hypnosis audio."""

import numpy as np
from scipy.signal import chirp


def generate_binaural_beat(
    duration_sec: float,
    sr: int = 44100,
    carrier_freq: float = 200,
    start_beat_freq: float = 14,
    end_beat_freq: float = 4,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Generate a binaural beat with frequency ramping.
    
    Creates stereo audio where:
    - Left ear: pure sine at carrier_freq
    - Right ear: chirp from (carrier_freq + start_beat_freq) to (carrier_freq + end_beat_freq)
    
    The frequency difference creates the binaural beat effect (e.g., 200Hz left, 214→204Hz right = 14→4Hz beat).
    
    Args:
        duration_sec: Duration in seconds
        sr: Sample rate (default 44100Hz)
        carrier_freq: Base frequency in Hz (default 200Hz)
        start_beat_freq: Initial beat frequency in Hz (default 14Hz - Beta)
        end_beat_freq: Final beat frequency in Hz (default 4Hz - Theta)
        rng: Random generator for reproducibility (currently unused but reserved for future extensions)
    
    Returns:
        Stereo array with shape (num_samples, 2), normalized to [-1.0, 1.0]
    """
    if rng is None:
        rng = np.random.default_rng()  # Reserved for future extensions
    
    num_samples = int(sr * duration_sec)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    
    # Left ear: pure sine at carrier frequency
    left = np.sin(2 * np.pi * carrier_freq * t)
    
    # Right ear: chirp from (carrier + start_beat) to (carrier + end_beat)
    # Using scipy.signal.chirp ensures phase continuity during the frequency ramp
    right = chirp(
        t,
        f0=carrier_freq + start_beat_freq,
        t1=duration_sec,
        f1=carrier_freq + end_beat_freq,
        method='linear',
        phi=0
    )
    
    # Combine into stereo array
    stereo = np.column_stack([left, right])
    
    # Normalize to [-1.0, 1.0]
    max_val = np.max(np.abs(stereo))
    if max_val > 0:
        stereo = stereo / max_val
    
    return stereo


def generate_pink_noise(num_samples: int, rng: np.random.Generator | None = None) -> np.ndarray:
    """Generate pink noise using FFT-based 1/f filtering.
    
    Pink noise has equal energy per octave (1/f power spectrum).
    
    Args:
        num_samples: Number of samples to generate
        rng: Random generator for reproducibility
    
    Returns:
        Mono array with shape (num_samples,), normalized to [-1.0, 1.0]
    """
    if rng is None:
        rng = np.random.default_rng()
    
    # Generate white noise
    white = rng.standard_normal(num_samples)
    
    # Apply 1/f filtering in frequency domain
    fft_white = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(num_samples)
    
    # Create 1/sqrt(f) filter (pink noise filter)
    # Avoid division by zero at DC component
    pink_filter = np.zeros_like(freqs)
    pink_filter[0] = 1.0  # DC component unchanged
    pink_filter[1:] = 1.0 / np.sqrt(freqs[1:])
    
    # Apply filter
    fft_pink = fft_white * pink_filter
    
    # Convert back to time domain
    pink = np.fft.irfft(fft_pink, n=num_samples)
    
    # Normalize to [-1.0, 1.0]
    max_val = np.max(np.abs(pink))
    if max_val > 0:
        pink = pink / max_val
    
    return pink


def generate_bed(
    duration_sec: float,
    sr: int = 44100,
    carrier_freq: float = 200,
    start_beat_freq: float = 14,
    end_beat_freq: float = 4,
    pink_noise_level: float = 0.3,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Generate a complete bed: binaural beat + pink noise.
    
    Combines a binaural beat with pink noise at the specified level.
    
    Args:
        duration_sec: Duration in seconds
        sr: Sample rate (default 44100Hz)
        carrier_freq: Base frequency for binaural beat (default 200Hz)
        start_beat_freq: Initial beat frequency (default 14Hz - Beta)
        end_beat_freq: Final beat frequency (default 4Hz - Theta)
        pink_noise_level: Pink noise mix level, 0.0-1.0 (default 0.3 = 30%)
        rng: Random generator for reproducibility
    
    Returns:
        Stereo array with shape (num_samples, 2), normalized to [-1.0, 1.0]
    """
    if rng is None:
        rng = np.random.default_rng()
    
    # Generate binaural beat
    binaural = generate_binaural_beat(
        duration_sec=duration_sec,
        sr=sr,
        carrier_freq=carrier_freq,
        start_beat_freq=start_beat_freq,
        end_beat_freq=end_beat_freq,
        rng=rng
    )
    
    # Generate pink noise (mono)
    num_samples = int(sr * duration_sec)
    pink = generate_pink_noise(num_samples, rng=rng)
    
    # Convert pink noise to stereo (same signal both channels)
    pink_stereo = np.column_stack([pink, pink])
    
    # Mix: (1 - level) * binaural + level * pink_noise
    # This ensures level=0 gives pure binaural, level=1 gives pure pink noise
    bed = (1 - pink_noise_level) * binaural + pink_noise_level * pink_stereo
    
    # Normalize to [-1.0, 1.0]
    max_val = np.max(np.abs(bed))
    if max_val > 0:
        bed = bed / max_val
    
    return bed
