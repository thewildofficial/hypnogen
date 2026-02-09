"""Tests for KPipeline caching in TTS synthesis module.

Verifies that KPipeline instances are cached by lang_code to avoid
expensive re-initialization on every synthesize() call.
"""
import numpy as np
import pytest
from unittest.mock import Mock, patch, call
from concurrent.futures import ThreadPoolExecutor

from hypnogen.core.tts import synthesize


def _make_mock_pipeline():
    """Create a mock pipeline that returns valid audio results."""
    mock_pipeline = Mock()
    mock_result = Mock()
    mock_audio = Mock()
    mock_audio.cpu.return_value.numpy.return_value = np.array([0.1, 0.2])
    mock_result.output.audio = mock_audio
    mock_pipeline.return_value = [mock_result]
    return mock_pipeline


class TestKPipelineCaching:
    """Test suite for KPipeline instance caching by lang_code."""

    @patch('hypnogen.core.tts.KPipeline')
    def test_same_lang_code_reuses_pipeline(self, mock_pipeline_class):
        """KPipeline should be constructed once for repeated calls with same lang_code."""
        mock_pipeline_class.return_value = _make_mock_pipeline()

        # Call 3 times with same voice (same lang_code 'a')
        synthesize("first call", voice="af_heart")
        synthesize("second call", voice="af_heart")
        synthesize("third call", voice="af_heart")

        # KPipeline constructor should be called only once
        assert mock_pipeline_class.call_count == 1
        mock_pipeline_class.assert_called_once_with(lang_code='a')

    @patch('hypnogen.core.tts.KPipeline')
    def test_different_lang_code_creates_new_pipeline(self, mock_pipeline_class):
        """KPipeline should be constructed again for a different lang_code."""
        mock_pipeline_class.return_value = _make_mock_pipeline()

        # Call with American English voice (lang_code 'a')
        synthesize("american english", voice="af_heart")
        # Call with British English voice (lang_code 'b')
        synthesize("british english", voice="bf_emma")

        # KPipeline constructor should be called twice (once per lang_code)
        assert mock_pipeline_class.call_count == 2
        mock_pipeline_class.assert_any_call(lang_code='a')
        mock_pipeline_class.assert_any_call(lang_code='b')

    @patch('hypnogen.core.tts.KPipeline')
    def test_same_lang_different_voices_reuses_pipeline(self, mock_pipeline_class):
        """Different voices with same lang_code should share one KPipeline."""
        mock_pipeline_class.return_value = _make_mock_pipeline()

        # af_heart and af_bella both have lang_code 'a'
        synthesize("voice one", voice="af_heart")
        synthesize("voice two", voice="af_bella")
        synthesize("voice three", voice="am_adam")

        # All share lang_code 'a' — only one KPipeline init
        assert mock_pipeline_class.call_count == 1

    @patch('hypnogen.core.tts.KPipeline')
    def test_multiple_lang_codes_each_cached_independently(self, mock_pipeline_class):
        """Each lang_code gets its own cached pipeline, reused on subsequent calls."""
        mock_pipeline_class.return_value = _make_mock_pipeline()

        # Interleave calls with different lang_codes
        synthesize("text", voice="af_heart")   # lang_code 'a'
        synthesize("text", voice="bf_emma")    # lang_code 'b'
        synthesize("text", voice="af_bella")   # lang_code 'a' (cached)
        synthesize("text", voice="bm_george")  # lang_code 'b' (cached)
        synthesize("text", voice="af_sarah")   # lang_code 'a' (cached)

        # Only 2 KPipeline constructions: one for 'a', one for 'b'
        assert mock_pipeline_class.call_count == 2

    @patch('hypnogen.core.tts.KPipeline')
    def test_concurrent_same_lang_code_single_init(self, mock_pipeline_class):
        """Concurrent calls with same lang_code should result in only 1 KPipeline init.

        This tests thread-safety of the caching mechanism. Multiple threads
        requesting the same lang_code simultaneously should not cause
        redundant KPipeline constructions.
        """
        mock_pipeline_class.return_value = _make_mock_pipeline()

        CONCURRENT_CALLS = 10

        with ThreadPoolExecutor(max_workers=CONCURRENT_CALLS) as executor:
            futures = [
                executor.submit(synthesize, f"text {i}", "af_heart")
                for i in range(CONCURRENT_CALLS)
            ]
            # Wait for all to complete and raise any exceptions
            for future in futures:
                future.result()

        # Despite concurrent access, KPipeline should only be initialized once
        assert mock_pipeline_class.call_count == 1
