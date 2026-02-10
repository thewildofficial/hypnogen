"""Abstract base class for TTS providers.

All TTS providers must implement the TTSProvider interface, which defines
a batch synthesis method and a shutdown hook for resource cleanup.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class TTSProvider(ABC):
    """Abstract TTS provider interface.

    Subclasses must implement synthesize_batch() to convert a list of text
    strings into audio arrays. The shutdown() method is called when the
    provider is no longer needed, allowing cleanup of resources like process
    pools or cached models.
    """

    @abstractmethod
    def synthesize_batch(
        self,
        texts: list[str],
        *,
        voice: str = "af_heart",
        speed: float = 1.0,
    ) -> list[tuple[np.ndarray, int]]:
        """Synthesize a batch of text strings to audio.

        Args:
            texts: List of text strings to synthesize.
            voice: Voice ID (e.g. "af_heart").
            speed: Speech speed multiplier (> 0).

        Returns:
            List of (audio_array, sample_rate) tuples, one per input text.
            Audio arrays are 1D float32 numpy arrays in [-1, 1] range.
            Order matches the input texts list.
        """

    def shutdown(self) -> None:
        """Release resources held by the provider.

        Default implementation is a no-op. Override in providers that hold
        process pools, model handles, or other heavyweight resources.
        """
