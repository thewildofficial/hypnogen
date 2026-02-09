"""Text-to-speech synthesis using Kokoro TTS.

This module provides a thin wrapper around the Kokoro TTS engine (pykokoro)
for converting text to speech. It returns audio as numpy arrays that can be
processed by other modules in the hypnogen pipeline.

Key features:
- 82M parameter Kokoro model with 54+ voices
- Native 24000Hz sample rate (can be overridden)
- Configurable voice selection (default: "af_heart" - female)
- Adjustable speech speed (0.5 = slower/hypnotic, 1.0 = normal, 2.0 = faster)
- Deterministic synthesis (no randomness)

Example:
    >>> audio, sr = synthesize("Welcome to deep relaxation", voice="af_heart", speed=0.8)
    >>> print(f"Generated {len(audio)} samples at {sr}Hz")
"""

from threading import Lock
from typing import Dict

import numpy as np
from kokoro import KPipeline


# Module-level cache: reuse KPipeline instances by lang_code
_pipeline_cache: Dict[str, KPipeline] = {}
_cache_lock = Lock()


# Known voices in Kokoro TTS (based on common patterns)
# This list represents the most common voice IDs
# Full list available at: https://huggingface.co/hexgrad/Kokoro-82M
KNOWN_VOICES = [
    # American English (a prefix)
    "af_heart",    # Female, warm and gentle (default)
    "af_bella",    # Female, expressive
    "af_nicole",   # Female, conversational
    "af_sarah",    # Female, professional
    "af_sky",      # Female, bright and clear
    "am_adam",     # Male, clear and steady
    "am_michael",  # Male, deep voice
    # British English (b prefix)
    "bf_emma",     # Female, British accent
    "bf_isabella", # Female, British accent, soft
    "bm_george",   # Male, British accent
    "bm_lewis",    # Male, British accent, warm
]


def _get_pipeline(lang_code: str) -> KPipeline:
    """Get or create a cached KPipeline for the given language code.

    Thread-safe: uses a lock to prevent redundant pipeline construction
    when multiple threads request the same lang_code concurrently.
    """
    with _cache_lock:
        if lang_code not in _pipeline_cache:
            _pipeline_cache[lang_code] = KPipeline(lang_code=lang_code)
        return _pipeline_cache[lang_code]


def synthesize(
    text: str,
    voice: str = "af_heart",
    speed: float = 1.0,
    sr: int = 24000
) -> tuple[np.ndarray, int]:
    """Synthesize text to speech using Kokoro TTS.
    
    Args:
        text: Text to synthesize. Cannot be empty or whitespace-only.
        voice: Voice ID to use (default: "af_heart" - female voice).
               Common voices: "af_heart" (female), "am_adam" (male).
               Voice ID format: <language><gender>_<name>
               e.g., "af" = American English Female
        speed: Speech speed multiplier (default: 1.0).
               Values: 0.5 = half speed (slower, more hypnotic)
                      1.0 = normal speed
                      2.0 = double speed
               Must be positive (> 0).
        sr: Target sample rate in Hz (default: 24000).
            Kokoro's native rate is 24000Hz. Other values accepted
            but the actual synthesis still happens at 24000Hz.
            Use audio resampling later in the pipeline if needed.
    
    Returns:
        Tuple of (audio, sample_rate) where:
        - audio: 1D numpy array of float32 samples in range [-1, 1]
        - sample_rate: int, the sample rate (24000 or custom value)
    
    Raises:
        ValueError: If text is empty/whitespace-only or speed <= 0
        RuntimeError: If Kokoro model is not available or download fails
    
    Example:
        >>> audio, sr = synthesize("Hello world", voice="af_heart", speed=0.9)
        >>> print(f"Audio shape: {audio.shape}, SR: {sr}")
        Audio shape: (72000,), SR: 24000
    
    Notes:
        - Synthesis is deterministic (no randomness)
        - Long text may be automatically chunked by Kokoro
        - Returns mono (1D) audio
        - Audio is normalized to [-1, 1] range
    """
    # Validate input
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    if speed <= 0:
        raise ValueError("Speed must be positive")
    
    # Extract language code from voice ID (first character)
    # e.g., "af_heart" -> "a", "bm_george" -> "b"
    lang_code = voice[0] if voice else "a"
    
    # Get cached Kokoro pipeline for the language
    # The pipeline will download the model on first use
    pipeline = _get_pipeline(lang_code)
    
    # Synthesize text to audio
    # The pipeline returns a generator of results
    audio_chunks = []
    for result in pipeline(text, voice=voice, speed=speed, split_pattern=r'\n+'):
        # Each result may contain audio output
        if result.output and result.output.audio is not None:
            # Convert torch tensor to numpy array
            audio_np = result.output.audio.cpu().numpy()
            audio_chunks.append(audio_np)
    
    # Concatenate all audio chunks into a single array
    if not audio_chunks:
        # Return empty array if no audio was generated
        return np.array([], dtype=np.float32), sr
    
    audio = np.concatenate(audio_chunks)
    
    return audio, sr


def list_voices() -> list[str]:
    """List available voice IDs for Kokoro TTS.
    
    Returns a list of known voice IDs that can be used with the
    synthesize() function. This is a curated list of common voices.
    
    For the full list of 54+ voices, see:
    https://huggingface.co/hexgrad/Kokoro-82M
    
    Returns:
        List of voice ID strings (e.g., ["af_heart", "am_adam", ...])
    
    Example:
        >>> voices = list_voices()
        >>> print(f"Available voices: {', '.join(voices[:3])}")
        Available voices: af_heart, am_adam, af_bella
    
    Notes:
        - Voice IDs follow format: <lang><gender>_<name>
        - Language codes: a=American English, b=British English,
          p=Portuguese, e=Spanish, f=French, i=Italian,
          h=Hindi, j=Japanese, z=Chinese
        - Gender codes: f=female, m=male
    """
    return KNOWN_VOICES.copy()
