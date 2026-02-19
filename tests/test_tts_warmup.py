"""Tests for TTS warmup functionality."""
import pytest
from unittest.mock import patch, MagicMock


class TestTTSWarmup:
    """Test warmup functionality - TDD."""

    def test_warmup_method_exists_on_quantized(self):
        """QuantizedProvider should have warmup method."""
        from hypnogen.core.tts_providers.quantized import QuantizedProvider

        provider = QuantizedProvider()
        assert hasattr(provider, 'warmup')
        assert callable(provider.warmup)

    def test_warmup_runs_synthesis(self):
        """warmup should trigger a synthesis call."""
        from hypnogen.core.tts_providers.quantized import QuantizedProvider

        provider = QuantizedProvider()

        with patch.object(provider, 'synthesize_batch') as mock_synth:
            mock_synth.return_value = [(MagicMock(), 24000)]
            provider.warmup()

            mock_synth.assert_called_once()
            args = mock_synth.call_args
            assert args[0][0] == ["warmup"]

    def test_warmup_returns_time(self):
        """warmup should return time taken."""
        from hypnogen.core.tts_providers.quantized import QuantizedProvider

        provider = QuantizedProvider()

        with patch.object(provider, 'synthesize_batch') as mock_synth:
            mock_synth.return_value = [(MagicMock(), 24000)]
            elapsed = provider.warmup()

            assert isinstance(elapsed, float)
            assert elapsed >= 0

    def test_warmup_tts_function_exists(self):
        """warmup_tts convenience function should exist."""
        from hypnogen.core.tts import warmup_tts
        assert callable(warmup_tts)

    def test_warmup_tts_creates_provider(self):
        """warmup_tts should create QuantizedProvider and warmup."""
        from hypnogen.core.tts import warmup_tts
        from hypnogen.core.tts_providers.quantized import QuantizedProvider

        with patch.object(QuantizedProvider, 'warmup') as mock_warmup:
            mock_warmup.return_value = 0.5
            elapsed = warmup_tts()

            mock_warmup.assert_called_once()
            assert elapsed == 0.5
