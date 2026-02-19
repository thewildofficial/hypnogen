"""TTS result caching layer.

Caches synthesized audio keyed by (text, voice, speed) hash.
Uses thread-safe LRU cache with automatic eviction.
"""

from __future__ import annotations

import hashlib
import logging
import threading
from typing import Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Thread-safe cache storage
_cache: Dict[str, tuple[np.ndarray, int]] = {}
_cache_lock = threading.Lock()
MAX_CACHE_SIZE = 100


def _make_key(text: str, voice: str, speed: float) -> str:
    """Create deterministic cache key."""
    key_str = f"{text}|{voice}|{speed:.4f}"
    return hashlib.md5(key_str.encode()).hexdigest()


def get_cached_tts(text: str, voice: str, speed: float) -> Optional[tuple[np.ndarray, int]]:
    """Get cached TTS result if available.

    Thread-safe read from cache.
    """
    key = _make_key(text, voice, speed)
    with _cache_lock:
        result = _cache.get(key)
        if result is not None:
            logger.debug(f"TTS cache hit: {key[:8]}...")
        return result


def cache_tts_result(
    text: str,
    voice: str,
    speed: float,
    audio: np.ndarray,
    sr: int,
) -> None:
    """Cache a TTS result.

    Thread-safe write with LRU eviction when cache is full.
    """
    key = _make_key(text, voice, speed)
    with _cache_lock:
        # Simple LRU: if full, remove oldest entry
        if len(_cache) >= MAX_CACHE_SIZE and key not in _cache:
            oldest_key = next(iter(_cache))
            del _cache[oldest_key]
            logger.debug(f"Cache evicted: {oldest_key[:8]}...")

        _cache[key] = (audio.copy(), sr)
        logger.debug(f"Cached TTS: {key[:8]}... (size: {len(_cache)})")


def clear_tts_cache() -> None:
    """Clear all cached TTS results."""
    global _cache
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
