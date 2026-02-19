"""Tests for TTS result caching."""
import pytest
import numpy as np


class TestTTSResultCache:
    """Test TTS result caching functionality - TDD."""

    def test_cache_module_imports(self):
        """Cache module should be importable with expected API."""
        from hypnogen.core import tts_result_cache
        assert hasattr(tts_result_cache, 'get_cached_tts')
        assert hasattr(tts_result_cache, 'cache_tts_result')
        assert hasattr(tts_result_cache, 'clear_tts_cache')
        assert hasattr(tts_result_cache, 'get_cache_stats')

    def test_cache_miss_returns_none(self):
        """Getting uncached text returns None."""
        from hypnogen.core.tts_result_cache import get_cached_tts, clear_tts_cache

        clear_tts_cache()
        result = get_cached_tts("not cached", "af_heart", 1.0, 24000)
        assert result is None

    def test_cache_hit_returns_audio(self):
        """Getting cached text returns audio tuple."""
        from hypnogen.core.tts_result_cache import (
            get_cached_tts, cache_tts_result, clear_tts_cache
        )

        clear_tts_cache()

        audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        sr = 24000

        cache_tts_result("hello", "af_heart", 1.0, sr, audio)
        result = get_cached_tts("hello", "af_heart", 1.0, sr)

        assert result is not None
        cached_audio, cached_sr = result
        assert cached_sr == sr
        np.testing.assert_array_equal(cached_audio, audio)

        clear_tts_cache()

    def test_cache_key_includes_voice(self):
        """Same text with different voices = separate cache entries."""
        from hypnogen.core.tts_result_cache import (
            get_cached_tts, cache_tts_result, clear_tts_cache
        )

        clear_tts_cache()

        audio1 = np.array([0.1, 0.2], dtype=np.float32)
        audio2 = np.array([0.3, 0.4], dtype=np.float32)

        cache_tts_result("hello", "af_heart", 1.0, 24000, audio1)
        cache_tts_result("hello", "am_adam", 1.0, 24000, audio2)

        result1 = get_cached_tts("hello", "af_heart", 1.0, 24000)
        result2 = get_cached_tts("hello", "am_adam", 1.0, 24000)

        assert result1 is not None
        assert result2 is not None
        np.testing.assert_array_equal(result1[0], audio1)
        np.testing.assert_array_equal(result2[0], audio2)

        clear_tts_cache()

    def test_cache_key_includes_speed(self):
        """Same text with different speeds = separate cache entries."""
        from hypnogen.core.tts_result_cache import (
            get_cached_tts, cache_tts_result, clear_tts_cache
        )

        clear_tts_cache()

        audio1 = np.array([0.1], dtype=np.float32)
        audio2 = np.array([0.2], dtype=np.float32)

        cache_tts_result("hello", "af_heart", 0.8, 24000, audio1)
        cache_tts_result("hello", "af_heart", 1.2, 24000, audio2)

        result1 = get_cached_tts("hello", "af_heart", 0.8, 24000)
        result2 = get_cached_tts("hello", "af_heart", 1.2, 24000)

        assert result1 is not None
        assert result2 is not None
        np.testing.assert_array_equal(result1[0], audio1)
        np.testing.assert_array_equal(result2[0], audio2)

        clear_tts_cache()

    def test_cache_stats(self):
        """Cache stats should track size."""
        from hypnogen.core.tts_result_cache import (
            get_cache_stats, clear_tts_cache, cache_tts_result
        )

        clear_tts_cache()

        stats = get_cache_stats()
        assert stats['size'] == 0

        audio = np.array([0.1], dtype=np.float32)
        cache_tts_result("test", "af_heart", 1.0, 24000, audio)

        stats = get_cache_stats()
        assert stats['size'] == 1

        clear_tts_cache()

    def test_clear_cache(self):
        """Clear cache removes all entries."""
        from hypnogen.core.tts_result_cache import (
            get_cached_tts, cache_tts_result, clear_tts_cache
        )

        audio = np.array([0.1], dtype=np.float32)
        cache_tts_result("test", "af_heart", 1.0, 24000, audio)
        assert get_cached_tts("test", "af_heart", 1.0, 24000) is not None

        clear_tts_cache()
        assert get_cached_tts("test", "af_heart", 1.0, 24000) is None

    def test_cached_audio_is_copy(self):
        """Cached audio should be a copy, not a reference."""
        from hypnogen.core.tts_result_cache import (
            get_cached_tts, cache_tts_result, clear_tts_cache
        )

        clear_tts_cache()

        original = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        cache_tts_result("test", "af_heart", 1.0, 24000, original)

        # Mutate original
        original[0] = 999.0

        result = get_cached_tts("test", "af_heart", 1.0, 24000)
        assert result is not None
        assert result[0][0] != 999.0  # Should not be affected

        clear_tts_cache()
