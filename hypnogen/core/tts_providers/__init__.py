"""TTS provider interface and implementations.

Provides a pluggable TTS backend strategy:
- PyTorchProvider: standard single-process Kokoro TTS (default)
- MultiprocessProvider: distributes TTS across N worker processes
- QuantizedProvider: applies dynamic INT8 quantization for speed
- CoreMLProvider: uses Apple Neural Engine for acceleration (macOS only)

Usage:
    from hypnogen.core.tts_providers import get_provider

    provider = get_provider("multiprocess", num_workers=3)
    results = provider.synthesize_batch(["hello", "world"], voice="af_heart", speed=0.9)
    provider.shutdown()
"""

from hypnogen.core.tts_providers.base import TTSProvider
from hypnogen.core.tts_providers.pytorch import PyTorchProvider
from hypnogen.core.tts_providers.multiprocess import MultiprocessProvider
from hypnogen.core.tts_providers.quantized import QuantizedProvider
from hypnogen.core.tts_providers.coreml import CoreMLProvider

_PROVIDERS = {
    "pytorch": PyTorchProvider,
    "multiprocess": MultiprocessProvider,
    "quantized": QuantizedProvider,
    "coreml": CoreMLProvider,
}


def get_provider(name: str = "pytorch", **kwargs) -> TTSProvider:
    """Create a TTS provider by name.

    Args:
        name: Provider name. One of "pytorch", "multiprocess", "quantized".
        **kwargs: Provider-specific keyword arguments (e.g. num_workers for multiprocess).

    Returns:
        An initialized TTSProvider instance.

    Raises:
        ValueError: If the provider name is unknown.
    """
    if name not in _PROVIDERS:
        available = ", ".join(sorted(_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown provider '{name}'. Available: {available}"
        )
    return _PROVIDERS[name](**kwargs)


__all__ = [
    "TTSProvider",
    "PyTorchProvider",
    "MultiprocessProvider",
    "QuantizedProvider",
    "CoreMLProvider",
    "get_provider",
]
