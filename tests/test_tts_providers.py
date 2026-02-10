"""Tests for TTS provider interface and implementations.

Tests cover:
- Base provider contract (abstract interface)
- PyTorchProvider: wraps existing synthesize() calls
- MultiprocessProvider: distributes TTS across worker processes
- QuantizedProvider: applies dynamic INT8 quantization
- Provider factory function
- synthesize_batch convenience function
"""

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_audio(n_samples: int = 2400) -> np.ndarray:
    """Return a small fake mono audio array."""
    return np.random.default_rng(0).uniform(-1, 1, n_samples).astype(np.float32)


def _make_synthesize_side_effect(n_samples: int = 2400):
    """Return a side_effect callable for mocking synthesize."""
    def _synth(text, voice="af_heart", speed=1.0, sr=24000):
        return _fake_audio(n_samples), sr
    return _synth


# ===========================================================================
# Base provider contract
# ===========================================================================


class TestBaseProvider:
    """Tests for the abstract TTSProvider base class."""

    def test_base_provider_cannot_be_instantiated(self):
        """TTSProvider is abstract and should not be instantiated directly."""
        from hypnogen.core.tts_providers.base import TTSProvider
        with pytest.raises(TypeError):
            TTSProvider()

    def test_base_provider_defines_synthesize_batch(self):
        """TTSProvider must define a synthesize_batch method."""
        from hypnogen.core.tts_providers.base import TTSProvider
        assert hasattr(TTSProvider, "synthesize_batch")

    def test_base_provider_defines_shutdown(self):
        """TTSProvider must define a shutdown method."""
        from hypnogen.core.tts_providers.base import TTSProvider
        assert hasattr(TTSProvider, "shutdown")


# ===========================================================================
# PyTorchProvider (standard, single-process)
# ===========================================================================


class TestPyTorchProvider:
    """Tests for the standard PyTorch TTS provider."""

    @patch("hypnogen.core.tts_providers.pytorch.synthesize")
    def test_synthesize_batch_returns_list_of_audio_arrays(self, mock_synth):
        """synthesize_batch returns a list of (audio, sr) tuples."""
        from hypnogen.core.tts_providers.pytorch import PyTorchProvider

        mock_synth.side_effect = _make_synthesize_side_effect()
        provider = PyTorchProvider()

        texts = ["hello", "world"]
        results = provider.synthesize_batch(texts, voice="af_heart", speed=0.9)

        assert len(results) == 2
        for audio, sr in results:
            assert isinstance(audio, np.ndarray)
            assert audio.ndim == 1
            assert sr == 24000

    @patch("hypnogen.core.tts_providers.pytorch.synthesize")
    def test_synthesize_batch_passes_voice_and_speed(self, mock_synth):
        """Voice and speed parameters are forwarded to synthesize."""
        from hypnogen.core.tts_providers.pytorch import PyTorchProvider

        mock_synth.side_effect = _make_synthesize_side_effect()
        provider = PyTorchProvider()

        provider.synthesize_batch(["test"], voice="am_adam", speed=0.7)

        mock_synth.assert_called_once_with("test", voice="am_adam", speed=0.7)

    @patch("hypnogen.core.tts_providers.pytorch.synthesize")
    def test_synthesize_batch_empty_list_returns_empty(self, mock_synth):
        """Empty text list returns empty result list."""
        from hypnogen.core.tts_providers.pytorch import PyTorchProvider

        provider = PyTorchProvider()
        results = provider.synthesize_batch([], voice="af_heart", speed=1.0)

        assert results == []
        mock_synth.assert_not_called()

    @patch("hypnogen.core.tts_providers.pytorch.synthesize")
    def test_synthesize_batch_single_text(self, mock_synth):
        """Single text item works correctly."""
        from hypnogen.core.tts_providers.pytorch import PyTorchProvider

        mock_synth.side_effect = _make_synthesize_side_effect()
        provider = PyTorchProvider()

        results = provider.synthesize_batch(["one item"], voice="af_heart", speed=1.0)
        assert len(results) == 1

    @patch("hypnogen.core.tts_providers.pytorch.synthesize")
    def test_synthesize_batch_preserves_order(self, mock_synth):
        """Results should be in the same order as input texts."""
        from hypnogen.core.tts_providers.pytorch import PyTorchProvider

        # Return different-length audio for each text to verify order
        mock_synth.side_effect = [
            (np.zeros(100, dtype=np.float32), 24000),
            (np.zeros(200, dtype=np.float32), 24000),
            (np.zeros(300, dtype=np.float32), 24000),
        ]
        provider = PyTorchProvider()

        results = provider.synthesize_batch(
            ["short", "medium", "long"], voice="af_heart", speed=1.0
        )

        assert len(results[0][0]) == 100
        assert len(results[1][0]) == 200
        assert len(results[2][0]) == 300

    def test_shutdown_is_noop(self):
        """PyTorchProvider.shutdown() should not raise."""
        from hypnogen.core.tts_providers.pytorch import PyTorchProvider

        provider = PyTorchProvider()
        provider.shutdown()  # Should not raise


# ===========================================================================
# MultiprocessProvider
# ===========================================================================


class TestMultiprocessProvider:
    """Tests for the multiprocessing TTS provider.

    Uses ThreadPoolExecutor via executor_factory injection to avoid
    pickling issues in tests (ProcessPoolExecutor requires picklable
    callables).
    """

    @patch("hypnogen.core.tts_providers.multiprocess._worker_synthesize")
    def test_synthesize_batch_distributes_work(self, mock_worker):
        """Work should be distributed to the executor pool."""
        from hypnogen.core.tts_providers.multiprocess import MultiprocessProvider

        mock_worker.return_value = (np.zeros(100, dtype=np.float32), 24000)

        provider = MultiprocessProvider(
            num_workers=2, executor_factory=ThreadPoolExecutor
        )
        try:
            texts = ["text1", "text2", "text3", "text4"]
            results = provider.synthesize_batch(texts, voice="af_heart", speed=0.9)

            assert len(results) == 4
            for audio, sr in results:
                assert isinstance(audio, np.ndarray)
                assert sr == 24000
        finally:
            provider.shutdown()

    @patch("hypnogen.core.tts_providers.multiprocess._worker_synthesize")
    def test_synthesize_batch_preserves_order(self, mock_worker):
        """Results must match input order even with parallel execution."""
        from hypnogen.core.tts_providers.multiprocess import MultiprocessProvider

        def _side_effect(text, voice, speed):
            length = len(text) * 100
            return (np.zeros(length, dtype=np.float32), 24000)

        mock_worker.side_effect = _side_effect

        provider = MultiprocessProvider(
            num_workers=2, executor_factory=ThreadPoolExecutor
        )
        try:
            texts = ["a", "bb", "ccc"]
            results = provider.synthesize_batch(texts, voice="af_heart", speed=1.0)

            assert len(results[0][0]) == 100
            assert len(results[1][0]) == 200
            assert len(results[2][0]) == 300
        finally:
            provider.shutdown()

    @patch("hypnogen.core.tts_providers.multiprocess._worker_synthesize")
    def test_synthesize_batch_empty_input(self, mock_worker):
        """Empty input returns empty results without spawning work."""
        from hypnogen.core.tts_providers.multiprocess import MultiprocessProvider

        provider = MultiprocessProvider(num_workers=2)
        try:
            results = provider.synthesize_batch([], voice="af_heart", speed=1.0)
            assert results == []
            mock_worker.assert_not_called()
        finally:
            provider.shutdown()

    def test_default_num_workers(self):
        """Default num_workers should be between 2 and 4."""
        from hypnogen.core.tts_providers.multiprocess import MultiprocessProvider

        provider = MultiprocessProvider()
        assert 2 <= provider.num_workers <= 4
        provider.shutdown()

    def test_custom_num_workers(self):
        """num_workers can be specified explicitly."""
        from hypnogen.core.tts_providers.multiprocess import MultiprocessProvider

        provider = MultiprocessProvider(num_workers=3)
        assert provider.num_workers == 3
        provider.shutdown()

    def test_shutdown_can_be_called_multiple_times(self):
        """Calling shutdown() multiple times should not raise."""
        from hypnogen.core.tts_providers.multiprocess import MultiprocessProvider

        provider = MultiprocessProvider(num_workers=2)
        provider.shutdown()
        provider.shutdown()  # Second call should be safe

    @patch("hypnogen.core.tts_providers.multiprocess._worker_synthesize")
    def test_worker_error_propagates(self, mock_worker):
        """If a worker raises, the error should propagate to the caller."""
        from hypnogen.core.tts_providers.multiprocess import MultiprocessProvider

        mock_worker.side_effect = RuntimeError("TTS model failed")

        # Single item path (direct call) — error propagates immediately
        provider = MultiprocessProvider(num_workers=2)
        try:
            with pytest.raises(RuntimeError, match="TTS model failed"):
                provider.synthesize_batch(["text"], voice="af_heart", speed=1.0)
        finally:
            provider.shutdown()

    @patch("hypnogen.core.tts_providers.multiprocess._worker_synthesize")
    def test_worker_error_propagates_in_pool(self, mock_worker):
        """If a pool worker raises, the error should propagate to the caller."""
        from hypnogen.core.tts_providers.multiprocess import MultiprocessProvider

        mock_worker.side_effect = RuntimeError("TTS model failed")

        provider = MultiprocessProvider(
            num_workers=2, executor_factory=ThreadPoolExecutor
        )
        try:
            with pytest.raises(RuntimeError, match="TTS model failed"):
                provider.synthesize_batch(
                    ["text1", "text2"], voice="af_heart", speed=1.0
                )
        finally:
            provider.shutdown()

    @patch("hypnogen.core.tts_providers.multiprocess._worker_synthesize")
    def test_single_text_does_not_use_pool(self, mock_worker):
        """A single text item should fall back to direct call, not pool."""
        from hypnogen.core.tts_providers.multiprocess import MultiprocessProvider

        mock_worker.return_value = (np.zeros(100, dtype=np.float32), 24000)

        provider = MultiprocessProvider(num_workers=2)
        try:
            results = provider.synthesize_batch(["solo"], voice="af_heart", speed=1.0)
            assert len(results) == 1
            # Pool should not have been created (lazy init)
            assert provider._pool is None
        finally:
            provider.shutdown()


# ===========================================================================
# QuantizedProvider
# ===========================================================================


class TestQuantizedProvider:
    """Tests for the quantized TTS provider wrapper."""

    @patch("hypnogen.core.tts_providers.quantized._get_pipeline")
    @patch("hypnogen.core.tts_providers.quantized.synthesize")
    def test_synthesize_batch_returns_valid_results(self, mock_synth, mock_get_pipeline):
        """Quantized provider should return valid audio results."""
        from hypnogen.core.tts_providers.quantized import QuantizedProvider

        mock_synth.side_effect = _make_synthesize_side_effect()
        mock_pipeline = Mock()
        mock_pipeline.model = None
        mock_get_pipeline.return_value = mock_pipeline

        provider = QuantizedProvider()
        results = provider.synthesize_batch(
            ["hello", "world"], voice="af_heart", speed=0.9
        )

        assert len(results) == 2
        for audio, sr in results:
            assert isinstance(audio, np.ndarray)
            assert sr == 24000

    @patch("hypnogen.core.tts_providers.quantized.synthesize")
    def test_synthesize_batch_empty_list(self, mock_synth):
        """Empty text list returns empty results."""
        from hypnogen.core.tts_providers.quantized import QuantizedProvider

        provider = QuantizedProvider()
        results = provider.synthesize_batch([], voice="af_heart", speed=1.0)
        assert results == []

    @patch("hypnogen.core.tts_providers.quantized._get_pipeline")
    @patch("hypnogen.core.tts_providers.quantized.synthesize")
    def test_quantization_applied_flag(self, mock_synth, mock_get_pipeline):
        """Provider should track whether quantization has been applied."""
        from hypnogen.core.tts_providers.quantized import QuantizedProvider

        mock_synth.side_effect = _make_synthesize_side_effect()
        # Mock pipeline with no model attribute to skip quantization gracefully
        mock_pipeline = Mock()
        mock_pipeline.model = None
        mock_get_pipeline.return_value = mock_pipeline

        provider = QuantizedProvider()
        assert provider.quantization_applied is False

        # After first synthesize_batch, quantization attempt should have been made
        provider.synthesize_batch(["test"], voice="af_heart", speed=1.0)
        # Flag is set to True after first call (even if quantization was a no-op)
        assert provider.quantization_applied is True

    @patch("hypnogen.core.tts_providers.quantized._get_pipeline")
    @patch("hypnogen.core.tts_providers.quantized.synthesize")
    def test_preserves_order(self, mock_synth, mock_get_pipeline):
        """Results order matches input order."""
        from hypnogen.core.tts_providers.quantized import QuantizedProvider

        mock_synth.side_effect = [
            (np.zeros(10, dtype=np.float32), 24000),
            (np.zeros(20, dtype=np.float32), 24000),
        ]
        mock_pipeline = Mock()
        mock_pipeline.model = None
        mock_get_pipeline.return_value = mock_pipeline

        provider = QuantizedProvider()
        results = provider.synthesize_batch(
            ["short", "longer"], voice="af_heart", speed=1.0
        )

        assert len(results[0][0]) == 10
        assert len(results[1][0]) == 20

    def test_shutdown_is_safe(self):
        """shutdown() should not raise."""
        from hypnogen.core.tts_providers.quantized import QuantizedProvider

        provider = QuantizedProvider()
        provider.shutdown()


# ===========================================================================
# Provider factory
# ===========================================================================


class TestProviderFactory:
    """Tests for the get_provider factory function."""

    def test_get_provider_pytorch(self):
        """get_provider('pytorch') returns PyTorchProvider."""
        from hypnogen.core.tts_providers import get_provider
        from hypnogen.core.tts_providers.pytorch import PyTorchProvider

        provider = get_provider("pytorch")
        assert isinstance(provider, PyTorchProvider)

    def test_get_provider_multiprocess(self):
        """get_provider('multiprocess') returns MultiprocessProvider."""
        from hypnogen.core.tts_providers import get_provider
        from hypnogen.core.tts_providers.multiprocess import MultiprocessProvider

        provider = get_provider("multiprocess")
        assert isinstance(provider, MultiprocessProvider)
        provider.shutdown()

    def test_get_provider_quantized(self):
        """get_provider('quantized') returns QuantizedProvider."""
        from hypnogen.core.tts_providers import get_provider
        from hypnogen.core.tts_providers.quantized import QuantizedProvider

        provider = get_provider("quantized")
        assert isinstance(provider, QuantizedProvider)

    def test_get_provider_default_is_pytorch(self):
        """Default provider (no argument) should be pytorch."""
        from hypnogen.core.tts_providers import get_provider
        from hypnogen.core.tts_providers.pytorch import PyTorchProvider

        provider = get_provider()
        assert isinstance(provider, PyTorchProvider)

    def test_get_provider_unknown_raises(self):
        """Unknown provider name raises ValueError."""
        from hypnogen.core.tts_providers import get_provider

        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("nonexistent")

    def test_get_provider_multiprocess_with_workers(self):
        """get_provider passes num_workers to MultiprocessProvider."""
        from hypnogen.core.tts_providers import get_provider
        from hypnogen.core.tts_providers.multiprocess import MultiprocessProvider

        provider = get_provider("multiprocess", num_workers=3)
        assert isinstance(provider, MultiprocessProvider)
        assert provider.num_workers == 3
        provider.shutdown()


# ===========================================================================
# Integration: synthesize_batch on tts module
# ===========================================================================


class TestSynthesizeBatch:
    """Tests for the top-level synthesize_batch convenience function."""

    def test_synthesize_batch_delegates_to_provider(self):
        """synthesize_batch should use the given provider."""
        from hypnogen.core.tts_providers.base import TTSProvider

        mock_provider = Mock(spec=TTSProvider)
        mock_provider.synthesize_batch.return_value = [
            (np.zeros(100, dtype=np.float32), 24000),
        ]

        from hypnogen.core.tts import synthesize_batch

        results = synthesize_batch(
            ["hello"], provider=mock_provider, voice="af_heart", speed=0.9
        )

        mock_provider.synthesize_batch.assert_called_once_with(
            ["hello"], voice="af_heart", speed=0.9
        )
        assert len(results) == 1

    @patch("hypnogen.core.tts_providers.pytorch.synthesize")
    def test_synthesize_batch_default_provider(self, mock_synth):
        """synthesize_batch with no provider uses PyTorchProvider."""
        mock_synth.side_effect = _make_synthesize_side_effect()

        from hypnogen.core.tts import synthesize_batch

        results = synthesize_batch(
            ["hello", "world"], voice="af_heart", speed=1.0
        )

        assert len(results) == 2
        assert mock_synth.call_count == 2
