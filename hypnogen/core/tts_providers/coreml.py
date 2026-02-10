"""CoreML provider for Kokoro TTS using Apple Neural Engine.

This provider uses CoreML models for TTS inference on Apple Silicon,
achieving significant speedup through ANE (Apple Neural Engine) acceleration.

Based on: https://github.com/mattmireles/kokoro-coreml

Requirements:
- CoreML models exported from Kokoro (Duration + Decoder)
- coremltools package
- macOS with Apple Silicon (M1/M2/M3)

Architecture:
1. Duration Model (CPU): Text tokens → duration predictions
2. Decoder Model (ANE): Features → Audio waveform (17x speedup)
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from .base import TTSProvider
from .pytorch import PyTorchProvider

if TYPE_CHECKING:
    import coremltools as ct


class CoreMLProvider(TTSProvider):
    """TTS provider using CoreML for accelerated inference on Apple Silicon.
    
    Falls back to PyTorchProvider if CoreML models are not available.
    
    Expected model structure:
        coreml_models/
            kokoro_duration.mlpackage          # Duration predictor
            kokoro_decoder_3s.mlpackage        # 3-second decoder
            kokoro_decoder_10s.mlpackage       # 10-second decoder  
            kokoro_decoder_45s.mlpackage       # 45-second decoder
    """

    def __init__(
        self,
        model_dir: str | Path | None = None,
        default_bucket: str = "3s",
    ) -> None:
        """Initialize CoreML provider.
        
        Args:
            model_dir: Directory containing CoreML models. If None, checks
                default locations (./coreml_models, ~/Library/Application Support/Hypnogen/Models)
            default_bucket: Default time bucket ("3s", "10s", or "45s")
        """
        self.model_dir = self._resolve_model_dir(model_dir)
        self.default_bucket = default_bucket
        self._duration_model: ct.models.MLModel | None = None
        self._decoder_models: dict[str, ct.models.MLModel] = {}
        self._pytorch_fallback = PyTorchProvider()
        self._models_loaded = False
        
        # Try to load models
        self._load_models()
    
    def _resolve_model_dir(self, model_dir: str | Path | None) -> Path:
        """Resolve model directory path."""
        if model_dir is not None:
            return Path(model_dir)
        
        # Check default locations
        locations = [
            Path("coreml_models"),
            Path.home() / "Library" / "Application Support" / "Hypnogen" / "Models",
            Path(__file__).parent.parent.parent.parent / "vendor" / "kokoro-coreml" / "coreml",
        ]
        
        for loc in locations:
            if loc.exists():
                return loc
        
        # Default to first location
        return locations[0]
    
    def _load_models(self) -> None:
        """Load CoreML models if available."""
        try:
            import coremltools as ct
        except ImportError:
            warnings.warn("coremltools not installed. CoreML provider will use PyTorch fallback.")
            return
        
        if not self.model_dir.exists():
            warnings.warn(
                f"CoreML models not found at {self.model_dir}. "
                "Provider will use PyTorch fallback. "
                "To use CoreML, export models from kokoro-coreml: "
                "https://github.com/mattmireles/kokoro-coreml"
            )
            return
        
        # Load duration model
        duration_path = self.model_dir / "kokoro_duration.mlpackage"
        if duration_path.exists():
            try:
                self._duration_model = ct.models.MLModel(str(duration_path))
                print(f"✅ Loaded CoreML duration model")
            except Exception as e:
                warnings.warn(f"Failed to load duration model: {e}")
        
        # Load decoder models
        for bucket in ["3s", "10s", "45s"]:
            decoder_path = self.model_dir / f"kokoro_decoder_{bucket}.mlpackage"
            if decoder_path.exists():
                try:
                    self._decoder_models[bucket] = ct.models.MLModel(str(decoder_path))
                    print(f"✅ Loaded CoreML decoder ({bucket})")
                except Exception as e:
                    warnings.warn(f"Failed to load decoder ({bucket}): {e}")
        
        self._models_loaded = (
            self._duration_model is not None 
            and len(self._decoder_models) > 0
        )
        
        if self._models_loaded:
            print(f"🚀 CoreML provider ready with ANE acceleration")
        else:
            print(f"⚠️  CoreML models not fully available, using PyTorch fallback")
    
    def _select_bucket(self, text: str) -> str:
        """Select appropriate time bucket based on text length."""
        # Rough estimate: ~15 chars per second at normal speed
        estimated_duration = len(text) / 15
        
        if estimated_duration <= 3:
            return "3s"
        elif estimated_duration <= 10:
            return "10s"
        else:
            return "45s"
    
    def synthesize_batch(
        self,
        texts: list[str],
        *,
        voice: str = "af_heart",
        speed: float = 1.0,
    ) -> list[tuple[np.ndarray, int]]:
        """Synthesize text using CoreML or fallback to PyTorch.
        
        Args:
            texts: List of text strings to synthesize
            voice: Voice ID (e.g., "af_heart")
            speed: Speech speed multiplier
            
        Returns:
            List of (audio_array, sample_rate) tuples
        """
        if not self._models_loaded:
            # Fallback to PyTorch
            return self._pytorch_fallback.synthesize_batch(
                texts, voice=voice, speed=speed
            )
        
        results = []
        for text in texts:
            try:
                audio = self._synthesize_coreml(text, voice, speed)
                results.append((audio, 24000))
            except Exception as e:
                warnings.warn(f"CoreML synthesis failed for '{text[:30]}...': {e}. Falling back to PyTorch.")
                # Fallback for this specific text
                fallback_result = self._pytorch_fallback.synthesize_batch(
                    [text], voice=voice, speed=speed
                )
                results.extend(fallback_result)
        
        return results
    
    def _synthesize_coreml(
        self, 
        text: str, 
        voice: str, 
        speed: float
    ) -> np.ndarray:
        """Synthesize single text using CoreML pipeline.
        
        This is a placeholder implementation. Full implementation requires:
        1. Tokenization (phoneme IDs from KPipeline)
        2. Duration prediction (CoreML)
        3. Alignment matrix construction
        4. Decoder inference (CoreML with ANE)
        5. Audio post-processing
        
        For now, falls back to PyTorch.
        """
        # TODO: Full CoreML pipeline implementation
        # This requires integration with kokoro-coreml's approach:
        # - G2P via KPipeline (keep in Python)
        # - Duration model inference
        # - Build alignment matrix  
        # - Decoder inference with bucket selection
        
        # For now, use fallback
        raise NotImplementedError(
            "Full CoreML pipeline not yet implemented. "
            "Falling back to PyTorch. "
            "To implement: integrate kokoro-coreml's two-stage approach."
        )
    
    def shutdown(self) -> None:
        """Release CoreML models and fallback."""
        self._duration_model = None
        self._decoder_models.clear()
        self._pytorch_fallback.shutdown()
    
    @property
    def is_using_coreml(self) -> bool:
        """Check if provider is actively using CoreML (not fallback)."""
        return self._models_loaded
    
    @property
    def available_buckets(self) -> list[str]:
        """List available time buckets."""
        return list(self._decoder_models.keys())
