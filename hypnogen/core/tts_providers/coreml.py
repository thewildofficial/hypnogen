"""CoreML hybrid Kokoro TTS provider.

This provider runs a hybrid inference pipeline:
1. Duration model (CoreML/ANE): token ids -> durations + intermediate features.
2. Prosody prediction (PyTorch CPU): F0Ntrain for F0/N curves.
3. Decoder model (CoreML/ANE): aligned features + F0/N -> waveform.

The PyTorch predictor is loaded lazily on first use for F0Ntrain computation.
If PyTorch/KModel is unavailable, falls back to the energy-derived heuristic.
"""

from __future__ import annotations

import json
import logging
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, Any

import numpy as np
from kokoro import KPipeline

from .base import TTSProvider

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import coremltools as ct


SAMPLE_RATE = 24000
MODEL_TOKEN_LIMIT_DEFAULT = 128
BOS_TOKEN_ID = 0
EOS_TOKEN_ID = 0
F0_SMOOTH_KERNEL = np.array([0.2, 0.6, 0.2], dtype=np.float32)
NOISE_BASELINE = 0.05
NOISE_VARIANCE = 0.01
EPSILON = 1e-6


@dataclass(frozen=True)
class DurationModelSpec:
    input_ids_name: str
    ref_s_name: str
    speed_name: str
    attention_mask_name: str
    pred_dur_name: str
    d_name: str
    t_en_name: str
    s_name: str
    token_limit: int


@dataclass(frozen=True)
class DecoderModelSpec:
    bucket_name: str
    seconds: int
    asr_name: str
    f0_name: str
    n_name: str
    ref_s_name: str
    waveform_name: str
    asr_shape: tuple[int, ...]
    f0_shape: tuple[int, ...]
    n_shape: tuple[int, ...]
    ref_s_shape: tuple[int, ...]
    waveform_shape: tuple[int, ...]
    asr_channels: int
    asr_frames: int
    f0_frames: int
    waveform_samples: int


class CoreMLProvider(TTSProvider):
    """CoreML-only TTS provider for Kokoro duration + decoder models."""

    _DECODER_FILENAMES = (
        "kokoro_decoder_only_3s.mlpackage",
        "kokoro_decoder_only_5s.mlpackage",
        "kokoro_decoder_only_10s.mlpackage",
    )

    def __init__(
        self,
        model_dir: str | Path | None = None,
        default_bucket: str = "3s",
        compute_units: str | Any | None = "ALL",
    ) -> None:
        self.model_dir = self._resolve_model_dir(model_dir)
        self.default_bucket = default_bucket
        self._ct = self._import_coremltools()
        self.compute_units_name, self._compute_units = self._resolve_compute_units(compute_units)
        self._duration_model: Any | None = None
        self._duration_spec: DurationModelSpec | None = None
        self._decoder_models: dict[str, Any] = {}
        self._decoder_specs: dict[str, DecoderModelSpec] = {}
        self._pipelines: dict[str, KPipeline] = {}
        self._vocab_by_repo: dict[str, dict[str, int]] = {}
        self._lock = Lock()
        self._pytorch_model: Any | None = None
        self._f0ntrain_available: bool = False

        self._load_models()
        self._warm_up_models()

    def _resolve_compute_units(self, compute_units: str | Any | None) -> tuple[str, Any]:
        ct = self._ct
        allowed_names = ("ALL", "CPU_AND_GPU", "CPU_ONLY")
        compute_unit_enum = ct.ComputeUnit

        if compute_units is None:
            compute_units = "ALL"

        if isinstance(compute_units, str):
            normalized = compute_units.upper()
            if normalized not in allowed_names:
                allowed_str = ", ".join(allowed_names)
                raise ValueError(
                    f"Invalid compute_units '{compute_units}'. Expected one of: {allowed_str}."
                )
            return normalized, getattr(compute_unit_enum, normalized)

        for name in allowed_names:
            if compute_units == getattr(compute_unit_enum, name):
                return name, compute_units

        allowed_str = ", ".join(allowed_names)
        raise ValueError(
            f"Invalid compute_units value '{compute_units}'. Expected one of: {allowed_str}."
        )

    @staticmethod
    def _import_coremltools() -> Any:
        try:
            import coremltools as ct
        except ImportError as exc:
            raise RuntimeError(
                "coremltools is required for CoreMLProvider but is not installed."
            ) from exc
        return ct

    def _resolve_model_dir(self, model_dir: str | Path | None) -> Path:
        if model_dir is not None:
            return Path(model_dir)

        candidates = [
            Path("coreml_models"),
            Path.home() / "Library" / "Application Support" / "Hypnogen" / "Models",
            Path(__file__).resolve().parents[3] / "coreml_models",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def _get_compiled_model_cache_path(self, source_path: Path) -> Path:
        """Get the cache path for a compiled model, ensuring cache directory exists."""
        cache_root = Path.home() / ".cache" / "hypnogen" / "coreml_compiled"
        cache_root.mkdir(parents=True, exist_ok=True)
        # Cache key based on source path and modification time
        mtime = source_path.stat().st_mtime
        cache_name = f"{source_path.stem}_{int(mtime)}.mlmodelc"
        return cache_root / cache_name

    def _load_mlmodel(self, path: Path) -> Any:
        # Prefer configured compute units so benchmarks can compare CPU/GPU vs ANE.
        ct = self._ct
        
        # If it's a .mlpackage, use persistent compiled cache to avoid ANE cold compile delays
        if path.suffix == ".mlpackage":
            cache_path = self._get_compiled_model_cache_path(path)
            
            if cache_path.exists():
                logger.info(f"[CoreML] Using cached compiled model: {cache_path}")
                try:
                    return ct.models.MLModel(str(cache_path), compute_units=self._compute_units)
                except Exception as e:
                    logger.warning(f"[CoreML] Failed to load cached model, will recompile: {e}")
                    # Remove corrupted cache
                    import shutil
                    shutil.rmtree(cache_path, ignore_errors=True)
            
            # Compile and cache
            logger.info(f"[CoreML] Loading model (this may take 10+ minutes on first run for ANE compilation): {path.name}")
            try:
                # Load the model - this triggers compilation internally
                model = ct.models.MLModel(str(path), compute_units=self._compute_units)
                # Get the compiled model path and copy to cache
                compiled_path = model.get_compiled_model_path()
                if compiled_path:
                    logger.info(f"[CoreML] Model compiled at: {compiled_path}")
                    logger.info(f"[CoreML] Copying to cache: {cache_path}")
                    import shutil
                    shutil.copytree(compiled_path, cache_path, dirs_exist_ok=True)
                    logger.info(f"[CoreML] Model cached successfully")
                return model
            except Exception as e:
                logger.error(f"[CoreML] Failed to compile model: {e}")
                # Fallback: try direct load (may still work if already compiled)
                logger.info(f"[CoreML] Falling back to direct load")
        
        # Direct load (for already-compiled .mlmodelc or if caching failed)
        try:
            return ct.models.MLModel(str(path), compute_units=self._compute_units)
        except TypeError:
            return ct.models.MLModel(str(path))

    def _load_models(self) -> None:
        if not self.model_dir.exists():
            raise FileNotFoundError(f"CoreML model directory not found: {self.model_dir}")

        duration_path = self.model_dir / "kokoro_duration.mlpackage"
        if not duration_path.exists():
            raise FileNotFoundError(
                f"Duration model not found at {duration_path}. "
                "Expected: kokoro_duration.mlpackage"
            )

        self._duration_model = self._load_mlmodel(duration_path)
        self._duration_spec = self._infer_duration_spec(self._duration_model)

        for decoder_filename in self._DECODER_FILENAMES:
            path = self.model_dir / decoder_filename
            if not path.exists():
                continue
            bucket_name = decoder_filename.removeprefix("kokoro_decoder_only_").removesuffix(".mlpackage")
            model = self._load_mlmodel(path)
            spec = self._infer_decoder_spec(model, bucket_name)
            self._decoder_models[bucket_name] = model
            self._decoder_specs[bucket_name] = spec

        if not self._decoder_models:
            expected = ", ".join(self._DECODER_FILENAMES)
            raise FileNotFoundError(
                f"No decoder-only CoreML buckets found in {self.model_dir}. "
                f"Expected one or more of: {expected}"
            )

        if self.default_bucket not in self._decoder_models:
            self.default_bucket = sorted(
                self._decoder_specs.keys(),
                key=lambda b: self._decoder_specs[b].seconds,
            )[0]

    @staticmethod
    def _collect_feature_shapes(model: Any) -> tuple[dict[str, tuple[int, ...]], dict[str, tuple[int, ...]]]:
        spec = model.get_spec().description
        inputs: dict[str, tuple[int, ...]] = {}
        outputs: dict[str, tuple[int, ...]] = {}
        for feature in spec.input:
            shape = tuple(int(v) for v in feature.type.multiArrayType.shape)
            inputs[feature.name] = shape
        for feature in spec.output:
            shape = tuple(int(v) for v in feature.type.multiArrayType.shape)
            outputs[feature.name] = shape
        return inputs, outputs

    @staticmethod
    def _find_name(
        available_names: list[str],
        exact_candidates: tuple[str, ...],
        contains_candidates: tuple[str, ...] = (),
    ) -> str | None:
        for name in exact_candidates:
            if name in available_names:
                return name
        lowered = {name: name.lower() for name in available_names}
        for candidate in contains_candidates:
            for name, name_lower in lowered.items():
                if candidate in name_lower:
                    return name
        return None

    def _infer_duration_spec(self, model: Any) -> DurationModelSpec:
        input_shapes, output_shapes = self._collect_feature_shapes(model)
        input_names = list(input_shapes.keys())
        output_names = list(output_shapes.keys())

        input_ids_name = self._find_name(input_names, ("input_ids",), ("input_ids", "ids"))
        ref_s_name = self._find_name(input_names, ("ref_s",), ("ref_s",))
        speed_name = self._find_name(input_names, ("speed",), ("speed",))
        attention_mask_name = self._find_name(input_names, ("attention_mask",), ("attention_mask", "mask"))

        pred_dur_name = self._find_name(output_names, ("pred_dur",), ("pred_dur", "duration"))
        d_name = self._find_name(output_names, ("d",), ("duration_hidden",))
        t_en_name = self._find_name(output_names, ("t_en",), ("t_en", "text_encoder"))
        s_name = self._find_name(output_names, ("s",), ("style",))

        if pred_dur_name is None:
            # Fallback: first rank-2 output that shares the token axis.
            for name, shape in output_shapes.items():
                if len(shape) == 2 and shape[-1] >= MODEL_TOKEN_LIMIT_DEFAULT:
                    pred_dur_name = name
                    break
        if t_en_name is None:
            # Fallback: rank-3 output with a likely text-encoder channel dimension.
            for name, shape in output_shapes.items():
                if len(shape) == 3 and (512 in shape or 256 in shape):
                    t_en_name = name
                    break
        if d_name is None:
            # Fallback: remaining rank-3 output.
            for name, shape in output_shapes.items():
                if len(shape) == 3 and name != t_en_name:
                    d_name = name
                    break
        if s_name is None:
            # Fallback: rank-2 style vector that is not pred_dur.
            for name, shape in output_shapes.items():
                if len(shape) == 2 and name != pred_dur_name:
                    s_name = name
                    break

        missing = [
            name
            for name, value in (
                ("input_ids", input_ids_name),
                ("ref_s", ref_s_name),
                ("speed", speed_name),
                ("attention_mask", attention_mask_name),
                ("pred_dur", pred_dur_name),
                ("d", d_name),
                ("t_en", t_en_name),
                ("s", s_name),
            )
            if value is None
        ]
        if missing:
            raise RuntimeError(
                "Duration model is missing expected features: "
                + ", ".join(missing)
            )

        token_limit = MODEL_TOKEN_LIMIT_DEFAULT
        shape = input_shapes[input_ids_name]
        if shape:
            token_limit = int(shape[-1])

        return DurationModelSpec(
            input_ids_name=input_ids_name,
            ref_s_name=ref_s_name,
            speed_name=speed_name,
            attention_mask_name=attention_mask_name,
            pred_dur_name=pred_dur_name,
            d_name=d_name,
            t_en_name=t_en_name,
            s_name=s_name,
            token_limit=token_limit,
        )

    def _infer_decoder_spec(self, model: Any, bucket_name: str) -> DecoderModelSpec:
        input_shapes, output_shapes = self._collect_feature_shapes(model)
        input_names = list(input_shapes.keys())
        output_names = list(output_shapes.keys())

        asr_name = self._find_name(input_names, ("asr",), ("asr",))
        f0_name = self._find_name(input_names, ("F0_pred", "f0_pred"), ("f0",))
        n_name = self._find_name(input_names, ("N_pred", "n_pred", "N", "n"), ("n_pred", "noise"))
        ref_s_name = self._find_name(input_names, ("ref_s",), ("ref_s", "style"))
        waveform_name = self._find_name(output_names, ("waveform",), ("waveform",))

        if n_name is None and asr_name is not None and f0_name is not None and ref_s_name is not None:
            remaining = [
                name for name in input_names if name not in {asr_name, f0_name, ref_s_name}
            ]
            if remaining:
                n_name = remaining[0]

        missing = [
            name
            for name, value in (
                ("asr", asr_name),
                ("F0_pred", f0_name),
                ("N_pred", n_name),
                ("ref_s", ref_s_name),
                ("waveform", waveform_name),
            )
            if value is None
        ]
        if missing:
            raise RuntimeError(
                f"Decoder model '{bucket_name}' is missing expected features: {', '.join(missing)}"
            )

        asr_shape = input_shapes[asr_name]
        f0_shape = input_shapes[f0_name]
        n_shape = input_shapes[n_name]
        ref_s_shape = input_shapes[ref_s_name]
        waveform_shape = output_shapes[waveform_name]

        if len(asr_shape) == 4 and asr_shape[1] == 1 and asr_shape[2] > 1:
            asr_channels = int(asr_shape[2])
        elif len(asr_shape) >= 2:
            asr_channels = int(asr_shape[1])
        else:
            asr_channels = 512
        asr_frames = int(asr_shape[-1]) if asr_shape else 0
        f0_frames = int(f0_shape[-1]) if f0_shape else 0
        waveform_samples = int(waveform_shape[-1]) if waveform_shape else SAMPLE_RATE
        seconds = int(bucket_name.removesuffix("s"))

        return DecoderModelSpec(
            bucket_name=bucket_name,
            seconds=seconds,
            asr_name=asr_name,
            f0_name=f0_name,
            n_name=n_name,
            ref_s_name=ref_s_name,
            waveform_name=waveform_name,
            asr_shape=asr_shape,
            f0_shape=f0_shape,
            n_shape=n_shape,
            ref_s_shape=ref_s_shape,
            waveform_shape=waveform_shape,
            asr_channels=asr_channels,
            asr_frames=asr_frames,
            f0_frames=f0_frames,
            waveform_samples=waveform_samples,
        )

    def _warm_up_models(self) -> None:
        if self._duration_model is None or self._duration_spec is None:
            raise RuntimeError("CoreML duration model is not initialized.")

        token_limit = self._duration_spec.token_limit
        dummy_ids = np.zeros((1, token_limit), dtype=np.int32)
        dummy_mask = np.zeros((1, token_limit), dtype=np.int32)
        dummy_ids[0, :2] = [BOS_TOKEN_ID, EOS_TOKEN_ID]
        dummy_mask[0, :2] = 1
        dummy_ref_s = np.zeros((1, 256), dtype=np.float32)
        dummy_speed = np.array([1.0], dtype=np.float32)

        duration_inputs = {
            self._duration_spec.input_ids_name: dummy_ids,
            self._duration_spec.attention_mask_name: dummy_mask,
            self._duration_spec.ref_s_name: dummy_ref_s,
            self._duration_spec.speed_name: dummy_speed,
        }
        self._duration_model.predict(duration_inputs)

        decoder_spec = self._decoder_specs[self.default_bucket]
        decoder_model = self._decoder_models[self.default_bucket]
        decoder_inputs = {
            decoder_spec.asr_name: np.zeros(decoder_spec.asr_shape, dtype=np.float32),
            decoder_spec.f0_name: np.zeros(decoder_spec.f0_shape, dtype=np.float32),
            decoder_spec.n_name: np.zeros(decoder_spec.n_shape, dtype=np.float32),
            decoder_spec.ref_s_name: np.zeros(decoder_spec.ref_s_shape, dtype=np.float32),
        }
        decoder_model.predict(decoder_inputs)

    def _ensure_pytorch_predictor(self) -> bool:
        if self._f0ntrain_available:
            return True
        if self._pytorch_model is not None:
            return False

        with self._lock:
            if self._f0ntrain_available:
                return True
            try:
                import torch
                from kokoro import KModel

                self._pytorch_model = KModel().to("cpu").eval()
                if (
                    hasattr(self._pytorch_model, "predictor")
                    and hasattr(self._pytorch_model.predictor, "F0Ntrain")
                ):
                    self._f0ntrain_available = True
                    logger.info("PyTorch predictor loaded for F0Ntrain (hybrid mode)")
                    return True
                logger.warning("KModel loaded but predictor.F0Ntrain not found")
                return False
            except Exception:
                logger.info(
                    "PyTorch KModel unavailable; using energy heuristic for F0/N"
                )
                self._pytorch_model = False  # sentinel to prevent retries
                return False

    def _get_pipeline(self, lang_code: str) -> KPipeline:
        with self._lock:
            if lang_code not in self._pipelines:
                self._pipelines[lang_code] = KPipeline(lang_code=lang_code, model=False)
            return self._pipelines[lang_code]

    def _get_vocab(self, pipeline: KPipeline) -> dict[str, int]:
        repo_id = getattr(pipeline, "repo_id", "hexgrad/Kokoro-82M")
        with self._lock:
            if repo_id in self._vocab_by_repo:
                return self._vocab_by_repo[repo_id]

        config_path: Path | None = None
        local_candidates = [
            self.model_dir / "config.json",
            Path("checkpoints/config.json"),
            Path("vendor/kokoro-coreml/checkpoints/config.json"),
        ]
        for candidate in local_candidates:
            if candidate.exists():
                config_path = candidate
                break

        if config_path is None:
            try:
                from huggingface_hub import hf_hub_download
            except ImportError as exc:
                raise RuntimeError(
                    "Could not load Kokoro vocab: huggingface_hub is unavailable "
                    "and no local config.json was found."
                ) from exc
            config_path = Path(hf_hub_download(repo_id=repo_id, filename="config.json"))

        with config_path.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        vocab = config.get("vocab")
        if not isinstance(vocab, dict):
            raise RuntimeError(f"Invalid Kokoro config vocab at {config_path}")
        normalized_vocab = {str(key): int(value) for key, value in vocab.items()}

        with self._lock:
            self._vocab_by_repo[repo_id] = normalized_vocab
        return normalized_vocab

    @staticmethod
    def _to_numpy(value: Any, *, dtype: np.dtype) -> np.ndarray:
        if hasattr(value, "detach"):
            value = value.detach()
        if hasattr(value, "cpu"):
            value = value.cpu()
        if hasattr(value, "numpy"):
            value = value.numpy()
        return np.asarray(value, dtype=dtype)

    @staticmethod
    def _normalize_ref_s(voice_pack: np.ndarray, phoneme_len: int) -> np.ndarray:
        if voice_pack.ndim == 3:
            # Shape (N, 1, 256) -> squeeze to (N, 256)
            voice_pack = voice_pack.squeeze(1)
        if voice_pack.ndim == 1:
            ref = voice_pack
        elif voice_pack.ndim == 2:
            index = max(0, min(phoneme_len - 1, voice_pack.shape[0] - 1))
            ref = voice_pack[index]
        else:
            raise RuntimeError(f"Unexpected voice embedding shape: {voice_pack.shape}")

        ref = ref.astype(np.float32, copy=False).reshape(-1)
        if ref.shape[0] < 256:
            padded = np.zeros((256,), dtype=np.float32)
            padded[: ref.shape[0]] = ref
            ref = padded
        elif ref.shape[0] > 256:
            ref = ref[:256]
        return ref.reshape(1, 256)

    @staticmethod
    def _prepare_duration_inputs(
        phonemes: str,
        vocab: dict[str, int],
        token_limit: int,
    ) -> tuple[np.ndarray, np.ndarray, int]:
        mapped = [vocab.get(symbol) for symbol in phonemes]
        token_ids = [token_id for token_id in mapped if token_id is not None]
        if not token_ids:
            raise RuntimeError("Tokenizer produced no valid Kokoro token IDs.")

        payload_limit = max(0, token_limit - 2)
        token_ids = token_ids[:payload_limit]
        sequence = [BOS_TOKEN_ID, *token_ids, EOS_TOKEN_ID]
        valid_tokens = len(sequence)

        input_ids = np.zeros((1, token_limit), dtype=np.int32)
        attention_mask = np.zeros((1, token_limit), dtype=np.int32)
        input_ids[0, :valid_tokens] = np.asarray(sequence, dtype=np.int32)
        attention_mask[0, :valid_tokens] = 1
        return input_ids, attention_mask, valid_tokens

    @staticmethod
    def _as_feature_tensor(value: Any) -> np.ndarray:
        arr = np.asarray(value)
        if arr.ndim == 0:
            return arr.reshape(1, 1)
        return arr

    @staticmethod
    def _canon_t_en(t_en: np.ndarray) -> np.ndarray:
        if t_en.ndim != 3:
            raise RuntimeError(f"Unexpected t_en rank: {t_en.ndim}")
        # Expected canonical shape: [1, channels, tokens], channels usually 512.
        if t_en.shape[1] in (512, 640, 256, 128):
            return t_en.astype(np.float32, copy=False)
        if t_en.shape[2] in (512, 640, 256, 128):
            return np.transpose(t_en, (0, 2, 1)).astype(np.float32, copy=False)
        # Last-resort heuristic: keep larger dim as channels.
        if t_en.shape[1] >= t_en.shape[2]:
            return t_en.astype(np.float32, copy=False)
        return np.transpose(t_en, (0, 2, 1)).astype(np.float32, copy=False)

    @staticmethod
    def _build_alignment(pred_dur: np.ndarray, token_count: int, target_frames: int) -> np.ndarray:
        durations = pred_dur[:token_count].astype(np.float32, copy=False)
        durations = np.maximum(durations, 0.0)
        total = float(np.sum(durations))
        if total <= EPSILON:
            durations = np.ones((token_count,), dtype=np.float32)
            total = float(token_count)

        raw = durations * (target_frames / total)
        scaled = np.floor(raw).astype(np.int32)
        remainder = int(target_frames - np.sum(scaled))
        if remainder > 0:
            fractional = raw - scaled
            order = np.argsort(-fractional)
            for index in order[:remainder]:
                scaled[index] += 1
        elif remainder < 0:
            order = np.argsort(-scaled)
            deficit = -remainder
            for index in order:
                if deficit <= 0:
                    break
                reducible = min(deficit, scaled[index])
                scaled[index] -= reducible
                deficit -= reducible

        indices = np.repeat(np.arange(token_count, dtype=np.int32), scaled)
        if indices.size < target_frames:
            pad_value = indices[-1] if indices.size else 0
            pad = np.full((target_frames - indices.size,), pad_value, dtype=np.int32)
            indices = np.concatenate([indices, pad], axis=0)
        elif indices.size > target_frames:
            indices = indices[:target_frames]

        alignment = np.zeros((token_count, target_frames), dtype=np.float32)
        alignment[indices, np.arange(target_frames)] = 1.0
        return alignment

    @staticmethod
    def _smooth_1d(values: np.ndarray) -> np.ndarray:
        if values.size <= 2:
            return values
        padded = np.pad(values, (1, 1), mode="edge")
        return np.convolve(padded, F0_SMOOTH_KERNEL, mode="valid")

    @staticmethod
    def _interpolate_to_length(values: np.ndarray, target_len: int) -> np.ndarray:
        if values.size == target_len:
            return values.astype(np.float32, copy=False)
        if values.size <= 1:
            return np.full((target_len,), float(values[0] if values.size else 0.0), dtype=np.float32)
        src = np.linspace(0.0, 1.0, num=values.size, endpoint=True)
        dst = np.linspace(0.0, 1.0, num=target_len, endpoint=True)
        return np.interp(dst, src, values).astype(np.float32)

    def _derive_f0_n(self, asr: np.ndarray, f0_frames: int) -> tuple[np.ndarray, np.ndarray]:
        warnings.warn(
            "_derive_f0_n is deprecated; use F0Ntrain via _ensure_pytorch_predictor",
            DeprecationWarning,
            stacklevel=2,
        )
        energy = np.sqrt(np.mean(np.square(asr), axis=1))[0]
        energy = self._smooth_1d(energy.astype(np.float32))
        min_energy = float(np.min(energy))
        max_energy = float(np.max(energy))
        normalized = (energy - min_energy) / (max_energy - min_energy + EPSILON)
        normalized = self._interpolate_to_length(normalized, f0_frames)

        f0_pred = (0.08 + 0.92 * normalized).astype(np.float32)
        n_pred = (NOISE_BASELINE + NOISE_VARIANCE * (1.0 - normalized)).astype(np.float32)
        return f0_pred.reshape(1, f0_frames), n_pred.reshape(1, f0_frames)

    def _compute_f0_n_f0ntrain(
        self,
        duration_outputs: dict[str, Any],
        alignment: np.ndarray,
        token_count: int,
        ref_s: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        import torch

        assert self._duration_spec is not None

        # Get d tensor from duration model output
        # d shape from CoreML: [1, time, 640] (batch, time, channels)
        # Need to transpose to [1, 640, time] for matmul
        d_raw = self._as_feature_tensor(duration_outputs[self._duration_spec.d_name])
        if d_raw.ndim != 3:
            raise RuntimeError(f"Unexpected d rank: {d_raw.ndim}, expected 3")
        
        # d from CoreML is [1, time, 640], transpose to [1, 640, time]
        if d_raw.shape[2] == 640:
            d_np = np.transpose(d_raw, (0, 2, 1)).astype(np.float32)
        elif d_raw.shape[1] == 640:
            d_np = d_raw.astype(np.float32, copy=False)
        else:
            # Try to identify which dim is channels (should be 640)
            if d_raw.shape[1] > d_raw.shape[2]:
                d_np = d_raw.astype(np.float32, copy=False)
            else:
                d_np = np.transpose(d_raw, (0, 2, 1)).astype(np.float32)
        
        s_np = self._as_feature_tensor(
            duration_outputs[self._duration_spec.s_name]
        ).astype(np.float32).reshape(1, -1)

        # F0Ntrain expects s = ref_s[:, 128:] (128 dims).
        # Duration model output 's' may be 128 or 256 dims depending on export.
        if s_np.shape[1] >= 256:
            s_np = s_np[:, 128:]
        elif s_np.shape[1] < 128:
            s_np = ref_s.astype(np.float32).reshape(1, -1)[:, 128:]

        # Compute en: [1, 640, time] @ [time, frames] = [1, 640, frames]
        en_np = np.matmul(d_np[:, :, :token_count], alignment).astype(np.float32)

        model = self._pytorch_model
        assert model is not None and model is not False

        with torch.no_grad():
            en_t = torch.from_numpy(en_np)
            s_t = torch.from_numpy(s_np)
            f0_out, n_out = model.predictor.F0Ntrain(en_t, s_t)
            return (
                f0_out.cpu().numpy().astype(np.float32),
                n_out.cpu().numpy().astype(np.float32),
            )

    @staticmethod
    def _bucket_seconds_from_pred_dur(pred_dur: np.ndarray, token_count: int) -> float:
        total_frames = float(np.sum(np.maximum(pred_dur[:token_count], 0.0)))
        return total_frames / 80.0

    def _select_bucket(self, predicted_seconds: float) -> DecoderModelSpec:
        ordered = sorted(self._decoder_specs.values(), key=lambda spec: spec.seconds)
        for spec in ordered:
            if predicted_seconds <= float(spec.seconds):
                return spec
        return ordered[-1]

    @staticmethod
    def _fit_asr_to_shape(asr: np.ndarray, decoder_spec: DecoderModelSpec) -> np.ndarray:
        asr = asr.astype(np.float32, copy=False)
        channels = decoder_spec.asr_channels
        frames = decoder_spec.asr_frames

        fitted = np.zeros((1, channels, frames), dtype=np.float32)
        use_channels = min(channels, asr.shape[1])
        use_frames = min(frames, asr.shape[2])
        fitted[:, :use_channels, :use_frames] = asr[:, :use_channels, :use_frames]

        if len(decoder_spec.asr_shape) == 4:
            target = np.zeros(decoder_spec.asr_shape, dtype=np.float32)
            if decoder_spec.asr_shape[1] == channels and decoder_spec.asr_shape[2] == 1:
                target[:, :, 0, :] = fitted
                return target
            if decoder_spec.asr_shape[1] == 1 and decoder_spec.asr_shape[2] == channels:
                target[:, 0, :, :] = fitted
                return target
            return fitted.reshape(decoder_spec.asr_shape)
        return fitted

    @staticmethod
    def _fit_curve_to_shape(curve: np.ndarray, target_shape: tuple[int, ...]) -> np.ndarray:
        curve = curve.astype(np.float32, copy=False)
        if len(target_shape) == 2:
            fitted = np.zeros(target_shape, dtype=np.float32)
            use = min(target_shape[-1], curve.shape[-1])
            fitted[:, :use] = curve[:, :use]
            return fitted
        if len(target_shape) == 4:
            fitted = np.zeros(target_shape, dtype=np.float32)
            use = min(target_shape[-1], curve.shape[-1])
            fitted[..., :use] = curve[:, None, None, :use]
            return fitted
        raise RuntimeError(f"Unsupported curve shape: {target_shape}")

    @staticmethod
    def _fit_ref_s_to_shape(ref_s: np.ndarray, target_shape: tuple[int, ...]) -> np.ndarray:
        ref_s = ref_s.astype(np.float32, copy=False)
        if target_shape == (256,):
            return ref_s.reshape(256)
        fitted = np.zeros(target_shape, dtype=np.float32)
        flat = ref_s.reshape(-1)
        limit = min(flat.shape[0], int(np.prod(target_shape)))
        fitted.reshape(-1)[:limit] = flat[:limit]
        return fitted

    def _synthesize_segment(
        self,
        phonemes: str,
        ref_s: np.ndarray,
        speed: float,
        vocab: dict[str, int],
    ) -> np.ndarray:
        if self._duration_model is None or self._duration_spec is None:
            raise RuntimeError("Duration model is not initialized.")

        t0 = time.perf_counter()
        logger.info("[CoreML] Starting synthesis segment, phonemes_len=%d", len(phonemes))

        input_ids, attention_mask, valid_tokens = self._prepare_duration_inputs(
            phonemes=phonemes,
            vocab=vocab,
            token_limit=self._duration_spec.token_limit,
        )
        logger.info("[CoreML] Prepared duration inputs, valid_tokens=%d", valid_tokens)

        duration_inputs = {
            self._duration_spec.input_ids_name: input_ids,
            self._duration_spec.attention_mask_name: attention_mask,
            self._duration_spec.ref_s_name: ref_s.astype(np.float32),
            self._duration_spec.speed_name: np.array([speed], dtype=np.float32),
        }

        t_dur = time.perf_counter()
        logger.info("[CoreML] Running duration model prediction...")
        try:
            duration_outputs = self._duration_model.predict(duration_inputs)
        except Exception as exc:
            raise RuntimeError("CoreML duration inference failed.") from exc
        t_dur_done = time.perf_counter()
        logger.info("[CoreML] Duration model done in %.3fs", t_dur_done - t_dur)

        pred_dur = self._as_feature_tensor(duration_outputs[self._duration_spec.pred_dur_name]).astype(np.float32)
        t_en = self._canon_t_en(self._as_feature_tensor(duration_outputs[self._duration_spec.t_en_name]))

        token_count = min(valid_tokens, int(pred_dur.shape[-1]), int(t_en.shape[-1]))
        if token_count <= 0:
            return np.zeros((0,), dtype=np.float32)

        predicted_seconds = self._bucket_seconds_from_pred_dur(pred_dur[0], token_count)
        decoder_spec = self._select_bucket(predicted_seconds)
        decoder_model = self._decoder_models[decoder_spec.bucket_name]

        t_align = time.perf_counter()
        alignment = self._build_alignment(
            pred_dur=pred_dur[0],
            token_count=token_count,
            target_frames=decoder_spec.asr_frames,
        )
        asr = np.matmul(t_en[:, :, :token_count], alignment).astype(np.float32)
        asr = self._fit_asr_to_shape(asr, decoder_spec)
        t_align_done = time.perf_counter()
        logger.info("[CoreML] Alignment computed, asr_shape=%s", asr.shape)

        t_f0 = time.perf_counter()
        if self._ensure_pytorch_predictor():
            logger.info("[CoreML] Computing F0/N using F0Ntrain...")
            f0_pred, n_pred = self._compute_f0_n_f0ntrain(
                duration_outputs, alignment, token_count, ref_s,
            )
        else:
            logger.info("[CoreML] Computing F0/N using energy heuristic...")
            f0_pred, n_pred = self._derive_f0_n(
                asr.reshape(1, decoder_spec.asr_channels, decoder_spec.asr_frames),
                decoder_spec.f0_frames,
            )
        t_f0_done = time.perf_counter()
        logger.info("[CoreML] F0/N computation done in %.3fs", t_f0_done - t_f0)

        f0_pred = self._fit_curve_to_shape(f0_pred, decoder_spec.f0_shape)
        n_pred = self._fit_curve_to_shape(n_pred, decoder_spec.n_shape)
        ref_s_fit = self._fit_ref_s_to_shape(ref_s, decoder_spec.ref_s_shape)

        decoder_inputs = {
            decoder_spec.asr_name: asr,
            decoder_spec.f0_name: f0_pred,
            decoder_spec.n_name: n_pred,
            decoder_spec.ref_s_name: ref_s_fit,
        }

        t_dec = time.perf_counter()
        logger.info("[CoreML] Running decoder model prediction (bucket=%s)...", decoder_spec.bucket_name)
        try:
            decoder_outputs = decoder_model.predict(decoder_inputs)
        except Exception as exc:
            raise RuntimeError(
                f"CoreML decoder inference failed for bucket {decoder_spec.bucket_name}."
            ) from exc
        t_dec_done = time.perf_counter()
        logger.info("[CoreML] Decoder model done in %.3fs", t_dec_done - t_dec)

        waveform = self._as_feature_tensor(decoder_outputs[decoder_spec.waveform_name]).astype(np.float32).reshape(-1)

        target_samples = int(round(predicted_seconds * SAMPLE_RATE))
        if target_samples > 0:
            waveform = waveform[: min(target_samples, waveform.shape[0])]

        logger.info("[CoreML] Synthesis segment complete, total_time=%.3fs, waveform_samples=%d", time.perf_counter() - t0, waveform.shape[0])

        logger.debug(
            "Segment timing: duration=%.3fs align=%.3fs f0n=%.3fs decoder=%.3fs total=%.3fs",
            t_dur_done - t_dur,
            t_align_done - t_align,
            t_f0_done - t_f0,
            t_dec_done - t_dec,
            time.perf_counter() - t0,
        )
        return waveform

    def _synthesize_coreml(self, text: str, voice: str, speed: float) -> np.ndarray:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")
        if speed <= 0:
            raise ValueError("Speed must be positive.")

        lang_code = voice[0] if voice else "a"
        pipeline = self._get_pipeline(lang_code)
        vocab = self._get_vocab(pipeline)

        try:
            voice_pack_raw = pipeline.load_voice(voice)
        except Exception as exc:
            raise RuntimeError(f"Failed to load Kokoro voice embedding '{voice}'.") from exc
        voice_pack = self._to_numpy(voice_pack_raw, dtype=np.float32)

        chunks: list[np.ndarray] = []
        for result in pipeline(text, voice=voice, speed=speed, split_pattern=r"\n+"):
            phonemes = result.phonemes
            if not phonemes:
                continue
            ref_s = self._normalize_ref_s(voice_pack, len(phonemes))
            chunk = self._synthesize_segment(
                phonemes=phonemes,
                ref_s=ref_s,
                speed=speed,
                vocab=vocab,
            )
            if chunk.size > 0:
                chunks.append(chunk)

        if not chunks:
            return np.zeros((0,), dtype=np.float32)
        return np.concatenate(chunks).astype(np.float32, copy=False)

    def synthesize_batch(
        self,
        texts: list[str],
        *,
        voice: str = "af_heart",
        speed: float = 1.0,
    ) -> list[tuple[np.ndarray, int]]:
        outputs: list[tuple[np.ndarray, int]] = []
        for index, text in enumerate(texts):
            try:
                audio = self._synthesize_coreml(text=text, voice=voice, speed=speed)
            except Exception as exc:
                raise RuntimeError(f"CoreML synthesis failed at batch index {index}.") from exc
            outputs.append((audio, SAMPLE_RATE))
        return outputs

    def shutdown(self) -> None:
        self._duration_model = None
        self._duration_spec = None
        self._decoder_models.clear()
        self._decoder_specs.clear()
        self._pipelines.clear()
        self._vocab_by_repo.clear()
        self._pytorch_model = None
        self._f0ntrain_available = False

    @property
    def is_using_coreml(self) -> bool:
        return self._duration_model is not None and bool(self._decoder_models)

    @property
    def available_buckets(self) -> list[str]:
        return sorted(self._decoder_specs.keys(), key=lambda bucket: self._decoder_specs[bucket].seconds)
