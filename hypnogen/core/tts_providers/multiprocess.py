"""Multiprocessing TTS provider.

Distributes TTS synthesis across N worker processes to bypass the GIL
and leverage multiple CPU cores. Each worker loads its own KPipeline,
keeping the model warm across calls.

For small batches (1 item), falls back to direct single-process synthesis
to avoid process-pool overhead.
"""

from __future__ import annotations

import os
from concurrent.futures import Executor, ProcessPoolExecutor
from typing import Callable, Optional

import numpy as np

from hypnogen.core.tts_providers.base import TTSProvider

# Clamp worker count between these bounds
MIN_WORKERS = 2
MAX_WORKERS = 4


def _worker_synthesize(
    text: str,
    voice: str,
    speed: float,
) -> tuple[np.ndarray, int]:
    """Synthesize a single text in a worker process.

    This function is the target for ProcessPoolExecutor. It imports
    synthesize lazily so each worker gets its own KPipeline instance
    (no cross-process model sharing needed).

    Args:
        text: Text to synthesize.
        voice: Voice ID.
        speed: Speech speed multiplier.

    Returns:
        (audio_array, sample_rate) tuple.
    """
    from hypnogen.core.tts import synthesize
    return synthesize(text, voice=voice, speed=speed)


class MultiprocessProvider(TTSProvider):
    """Multi-process TTS provider using ProcessPoolExecutor.

    Spawns N worker processes, each with its own KPipeline. Work items
    (texts) are distributed across workers, results are collected in
    input order.

    For batches of 1 item, synthesis runs directly via _worker_synthesize
    in the calling process to avoid pool overhead.

    Args:
        num_workers: Number of worker processes. Defaults to
            min(cpu_count, MAX_WORKERS), clamped to [MIN_WORKERS, MAX_WORKERS].
        executor_factory: Optional callable that creates an Executor instance.
            Defaults to ProcessPoolExecutor. Override for testing with
            ThreadPoolExecutor.
    """

    def __init__(
        self,
        num_workers: Optional[int] = None,
        executor_factory: Optional[Callable[..., Executor]] = None,
    ) -> None:
        if num_workers is None:
            cpu_count = os.cpu_count() or MIN_WORKERS
            num_workers = max(MIN_WORKERS, min(cpu_count, MAX_WORKERS))
        self.num_workers = num_workers
        self._executor_factory = executor_factory or ProcessPoolExecutor
        self._pool: Optional[Executor] = None

    def _get_pool(self) -> Executor:
        """Lazily create the executor pool on first use."""
        if self._pool is None:
            self._pool = self._executor_factory(max_workers=self.num_workers)
        return self._pool

    def synthesize_batch(
        self,
        texts: list[str],
        *,
        voice: str = "af_heart",
        speed: float = 1.0,
    ) -> list[tuple[np.ndarray, int]]:
        """Synthesize texts in parallel across worker processes.

        For a single text, delegates directly to _worker_synthesize in the
        current process. For multiple texts, fans out to the executor pool
        and collects results in input order.

        Args:
            texts: List of text strings to synthesize.
            voice: Voice ID (e.g. "af_heart").
            speed: Speech speed multiplier (> 0).

        Returns:
            List of (audio_array, sample_rate) tuples in input order.

        Raises:
            RuntimeError: If any worker process fails.
        """
        if not texts:
            return []

        # Single item: avoid pool overhead
        if len(texts) == 1:
            result = _worker_synthesize(texts[0], voice, speed)
            return [result]

        # Multiple items: distribute across workers
        pool = self._get_pool()
        futures = [
            pool.submit(_worker_synthesize, text, voice, speed)
            for text in texts
        ]

        results: list[tuple[np.ndarray, int]] = []
        for future in futures:
            results.append(future.result())
        return results

    def shutdown(self) -> None:
        """Shut down the executor pool, releasing worker processes."""
        if self._pool is not None:
            self._pool.shutdown(wait=False)
            self._pool = None
