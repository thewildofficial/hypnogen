"""Test that default TTS provider is Quantized."""
import pytest
from unittest.mock import patch, MagicMock


class TestDefaultProvider:
    """Verify default provider switched from PyTorch to Quantized."""

    def test_default_provider_is_quantized(self):
        """synthesize_batch with no provider should use QuantizedProvider."""
        from hypnogen.core.tts import synthesize_batch
        from hypnogen.core.tts_providers.quantized import QuantizedProvider

        with patch.object(QuantizedProvider, 'synthesize_batch') as mock_synth:
            mock_synth.return_value = [(MagicMock(), 24000)]
            synthesize_batch(["test"], voice="af_heart")

            mock_synth.assert_called_once()

    def test_explicit_provider_overrides_default(self):
        """Explicit provider should be used when provided."""
        from hypnogen.core.tts import synthesize_batch
        from hypnogen.core.tts_providers.pytorch import PyTorchProvider

        with patch.object(PyTorchProvider, 'synthesize_batch') as mock_synth:
            mock_synth.return_value = [(MagicMock(), 24000)]
            synthesize_batch(["test"], provider=PyTorchProvider())

            mock_synth.assert_called_once()
