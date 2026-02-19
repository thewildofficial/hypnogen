"""TTS result caching layer.

Caches synthesized audio keyed by (text, voice, speed, sr) hash.
Uses thread-safe LRU cache with automatic eviction.
"""

from __future__ import annotations

import hashlib
import logging
import os
import threading
from collections import OrderedDict
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Thread-safe cache storage with true LRU behavior
MAX_CACHE_SIZE = int(os.environ.get("HYPNOGEN_TTS_CACHE_SIZE", 100))
_cache: OrderedDict[str, tuple[np.ndarray, int]] = OrderedDict()
_cache_lock = threading.Lock()


def _make_key(text: str, voice: str, speed: float, sr: int) -> str:
    """Create deterministic cache key."""
    key_str = f"{text}|{voice}|{speed:.4f}|{sr}"
    return hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()


def get_cached_tts(text: str, voice: str, speed: float, sr: int) -> Optional[tuple[np.ndarray, int]]:
    """Get cached TTS result if available.

    Thread-safe read from cache with true LRU promotion.
    Returns a defensive copy to prevent cache mutation.
    """
    key = _make_key(text, voice, speed, sr)
    with _cache_lock:
        result = _cache.get(key)
        if result is not None:
            # Promote to most-recently-used
            _cache.move_to_end(key)
            logger.debug(f"TTS cache hit: {key[:8]}...")
            # Return defensive copy to prevent cache mutation
            audio, cached_sr = result
            return (audio.copy(), cached_sr)
        return result


def cache_tts_result(
    text: str,
    voice: str,
    speed: float,
    sr: int,
    audio: np.ndarray,
) -> None:
    """Cache a TTS result.

    Thread-safe write with LRU eviction when cache is full.
    Stores a defensive copy of the audio array.
    """
    key = _make_key(text, voice, speed, sr)
    with _cache_lock:
        # If full, remove oldest (least recently used) entry
        if len(_cache) >= MAX_CACHE_SIZE and key not in _cache:
            oldest_key = next(iter(_cache))
            del _cache[oldest_key]
            logger.debug("Cache evicted: %s...", oldest_key[:8])

        _cache[key] = (audio.copy(), sr)
        logger.debug("Cached TTS: %s... (size: %d)", key[:8], len(_cache))


def clear_tts_cache() -> None:
    """Clear all cached TTS results."""
    with _cache_lock:
        _cache.clear()
    logger.info("TTS cache cleared")


def get_cache_stats() -> dict:
    """Get cache statistics."""
    with _cache_lock:
        return {
            "size": len(_cache),
            "max_size": MAX_CACHE_SIZE,
            "utilization": len(_cache) / MAX_CACHE_SIZE,
        }
