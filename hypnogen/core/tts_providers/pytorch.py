"""Standard PyTorch TTS provider.

Wraps the existing hypnogen.core.tts.synthesize() function in the
TTSProvider interface. This is the default provider — single-process,
sequential synthesis with the cached KPipeline.
"""

from __future__ import annotations

import numpy as np

from hypnogen.core.tts import synthesize
from hypnogen.core.tts_providers.base import TTSProvider


class PyTorchProvider(TTSProvider):
    """Single-process PyTorch TTS provider using Kokoro KPipeline.

    Delegates each text to the existing synthesize() function, which
    internally caches KPipeline instances by lang_code. This provider
    is the baseline: simple, correct, and predictable.
    """

    def synthesize_batch(
        self,
        texts: list[str],
        *,
        voice: str = "af_heart",
        speed: float = 1.0,
    ) -> list[tuple[np.ndarray, int]]:
        """Synthesize texts sequentially using Kokoro KPipeline.

        Args:
            texts: List of text strings to synthesize.
            voice: Voice ID (e.g. "af_heart").
            speed: Speech speed multiplier (> 0).

        Returns:
            List of (audio_array, sample_rate) tuples in input order.
        """
        results: list[tuple[np.ndarray, int]] = []
        for text in texts:
            audio, sr = synthesize(text, voice=voice, speed=speed)
            results.append((audio, sr))
        return results
