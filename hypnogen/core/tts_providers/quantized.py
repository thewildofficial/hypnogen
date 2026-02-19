"""Quantized TTS provider with dynamic INT8 quantization.

Applies torch.quantization.quantize_dynamic to the Kokoro model's
Linear and LSTM layers on first use. This reduces memory bandwidth
and can speed up inference on CPU, especially for larger batch sizes.

Quantization is applied lazily (on the first synthesize_batch call)
to avoid slowing down import time.
"""

from __future__ import annotations

import logging
from threading import Lock

import numpy as np
import torch

from hypnogen.core.tts import synthesize, _get_pipeline
from hypnogen.core.tts_providers.base import TTSProvider

logger = logging.getLogger(__name__)

# Layers eligible for dynamic quantization
_QUANTIZABLE_LAYERS = {torch.nn.Linear, torch.nn.LSTM}


class QuantizedProvider(TTSProvider):
    """TTS provider with dynamic INT8 quantization.

    On the first call to synthesize_batch(), applies
    torch.quantization.quantize_dynamic to the underlying Kokoro model's
    Linear and LSTM layers. Subsequent calls benefit from the quantized
    model.

    Quantization is a one-time cost (~0.5s) that pays off across many
    synthesis calls via reduced memory bandwidth.
    """

    def __init__(self) -> None:
        self._quantization_lock = Lock()
        self.quantization_applied: bool = False

    def _apply_quantization(self, lang_code: str) -> None:
        """Apply dynamic quantization to the cached pipeline's model.

        Thread-safe: only one thread will perform quantization, others
        will wait and skip if already done.

        Args:
            lang_code: Language code to get the pipeline for.
        """
        with self._quantization_lock:
            if self.quantization_applied:
                return

            try:
                pipeline = _get_pipeline(lang_code)
                model = getattr(pipeline, "model", None)

                if model is not None and isinstance(model, torch.nn.Module):
                    quantized_model = torch.quantization.quantize_dynamic(
                        model,
                        _QUANTIZABLE_LAYERS,
                        dtype=torch.qint8,
                    )
                    pipeline.model = quantized_model
                    logger.info(
                        "Applied dynamic INT8 quantization to Kokoro model "
                        "(lang_code=%s)",
                        lang_code,
                    )
                else:
                    logger.info(
                        "Kokoro pipeline has no quantizable model attribute; "
                        "skipping quantization (lang_code=%s)",
                        lang_code,
                    )
            except Exception:
                logger.warning(
                    "Dynamic quantization failed; falling back to unquantized "
                    "inference",
                    exc_info=True,
                )
            finally:
                # Mark as applied regardless — don't retry on failure
                self.quantization_applied = True

    def synthesize_batch(
        self,
        texts: list[str],
        *,
        voice: str = "af_heart",
        speed: float = 1.0,
    ) -> list[tuple[np.ndarray, int]]:
        """Synthesize texts using a dynamically quantized model.

        On the first call, applies INT8 quantization to the Kokoro model.
        Then delegates to the standard synthesize() function which uses
        the (now-quantized) cached pipeline.

        Args:
            texts: List of text strings to synthesize.
            voice: Voice ID (e.g. "af_heart").
            speed: Speech speed multiplier (> 0).

        Returns:
            List of (audio_array, sample_rate) tuples in input order.
        """
        if not texts:
            return []

        # Apply quantization on first call
        if not self.quantization_applied:
            lang_code = voice[0] if voice else "a"
            self._apply_quantization(lang_code)

        results: list[tuple[np.ndarray, int]] = []
        for text in texts:
            audio, sr = synthesize(text, voice=voice, speed=speed)
            results.append((audio, sr))
        return results

    def warmup(self, voice: str = "af_heart", speed: float = 1.0) -> float:
        """Warm up the quantized model to reduce cold-start latency.

        Performs a dummy synthesis to trigger quantization and model loading.

        Returns:
            Time taken for warmup in seconds.
        """
        import time
        start = time.perf_counter()

        try:
            _ = self.synthesize_batch(["warmup"], voice=voice, speed=speed)
            elapsed = time.perf_counter() - start
            logger.info(f"Quantized model warmup complete in {elapsed:.3f}s")
            return elapsed
        except Exception as e:
            logger.warning(f"Warmup failed: {e}")
            return 0.0
