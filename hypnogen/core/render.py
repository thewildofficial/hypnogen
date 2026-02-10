"""Unified render-core entry point for hypnosis audio generation.

Provides a single render_session() function that orchestrates the full pipeline:
parse → shepherd TTS → swarm TTS → binaural bed → mix → export.

This module is the canonical entry point used by CLI, Gradio UI, and the
upcoming FastAPI render worker. All callers delegate to this function
rather than duplicating the orchestration logic.
"""

from __future__ import annotations

import os
from typing import Any, Callable

import librosa
import numpy as np

from hypnogen.core.binaural import generate_bed
from hypnogen.core.effects import apply_analog_marking
from hypnogen.core.epochs import EPOCH_BOUNDARIES, select_boundary_events
from hypnogen.core.export import (
    create_render_metadata,
    write_metadata,
    write_wav,
)
from hypnogen.core.mixer import mix_layers
from hypnogen.core.parser import parse_script
from hypnogen.core.swarm import generate_swarm
from hypnogen.core.tts import synthesize

TTS_SAMPLE_RATE = 24000
DEFAULT_OUTPUT_SR = 44100
DEFAULT_VOICE = "af_heart"
DEFAULT_LENGTH_SEC = 600

# Progress fraction allocations for each pipeline stage
_PROGRESS_PARSE = 0.0
_PROGRESS_SHEPHERD_START = 0.02
_PROGRESS_SHEPHERD_END = 0.55
_PROGRESS_SWARM_START = 0.55
_PROGRESS_SWARM_END = 0.85
_PROGRESS_BED = 0.88
_PROGRESS_MIX = 0.93
_PROGRESS_EXPORT = 0.97
_PROGRESS_DONE = 1.0

# Type alias for the optional progress callback
ProgressCallback = Callable[[float, str], None]


def render_session(
    script_text: str,
    affirmations: list[str],
    output_dir: str,
    *,
    voice: str = DEFAULT_VOICE,
    swarm_voice: str | None = None,
    seed: int | None = None,
    length_sec: int | None = None,
    sr: int = DEFAULT_OUTPUT_SR,
    export_stems: bool = False,
    gain_db: dict[str, float] | None = None,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Orchestrate the full hypnosis audio render pipeline.

    This is the single entry point for all render operations. CLI, Gradio,
    and FastAPI all delegate to this function.

    Args:
        script_text: Raw script with optional XML-style tags (<cmd>, <pause>, etc.).
        affirmations: List of validated affirmation strings.
        output_dir: Directory where all output files are written.
        voice: TTS voice for shepherd track (default: "af_heart").
        swarm_voice: TTS voice for swarm track (defaults to same as voice).
        seed: Random seed for reproducibility (None = random).
        length_sec: Session length in seconds. If None, derived from shepherd
            audio length (minimum 60s).
        sr: Output sample rate (default: 44100).
        export_stems: Whether to write individual stem WAV files.
        gain_db: Per-layer gain overrides in dB (e.g. {"swarm": -24.0}).
        progress_callback: Optional callback(fraction, description) for progress.

    Returns:
        Dict with two keys:
        - "paths": {"mix": str, "stems": dict[str, str], "metadata": str}
        - "metadata": dict with seed, duration_sec, sample_rate, voices, etc.
    """
    if swarm_voice is None:
        swarm_voice = voice

    rng = np.random.default_rng(seed)
    os.makedirs(output_dir, exist_ok=True)

    _report_progress(progress_callback, _PROGRESS_PARSE, "Parsing script...")

    # 1. Parse
    segments = parse_script(script_text)

    # 2. Shepherd TTS
    _report_progress(progress_callback, _PROGRESS_SHEPHERD_START, "Shepherd TTS: starting...")
    shepherd_audio = _render_shepherd(
        segments,
        voice,
        sr,
        rng=rng,
        progress_callback=progress_callback,
        progress_offset=_PROGRESS_SHEPHERD_START,
        progress_scale=_PROGRESS_SHEPHERD_END - _PROGRESS_SHEPHERD_START,
    )

    # Determine session length
    effective_length_sec = _determine_length(shepherd_audio, sr, length_sec)

    # 3. Swarm TTS
    _report_progress(progress_callback, _PROGRESS_SWARM_START, "Swarm TTS: starting...")
    swarm_audio = _render_swarm(
        affirmations,
        effective_length_sec,
        sr,
        swarm_voice,
        rng,
        progress_callback=progress_callback,
        progress_offset=_PROGRESS_SWARM_START,
        progress_scale=_PROGRESS_SWARM_END - _PROGRESS_SWARM_START,
    )

    # 4. Binaural bed
    _report_progress(progress_callback, _PROGRESS_BED, "Generating binaural bed...")
    bed_audio = generate_bed(duration_sec=effective_length_sec, sr=sr, rng=rng)

    # 5. Pad/trim all layers to target length
    target_samples = effective_length_sec * sr
    shepherd_audio = _pad_or_trim(shepherd_audio, target_samples)
    swarm_audio = _pad_or_trim(swarm_audio, target_samples)
    bed_audio = _pad_or_trim(bed_audio, target_samples)

    # 6. Mix
    _report_progress(progress_callback, _PROGRESS_MIX, "Mixing layers & applying epochs...")
    boundary_events = select_boundary_events(rng)
    mixed = mix_layers(
        shepherd=shepherd_audio,
        swarm=swarm_audio,
        bed=bed_audio,
        sr=sr,
        gain_db=gain_db,
        apply_epochs=True,
        boundary_events=boundary_events,
        rng=rng,
    )

    # 7. Export
    _report_progress(progress_callback, _PROGRESS_EXPORT, "Exporting WAV...")

    mix_path = os.path.join(output_dir, "mix.wav")
    write_wav(mix_path, mixed, sr)

    # Build paths result
    paths: dict[str, Any] = {"mix": mix_path, "stems": {}}

    if export_stems:
        stems_paths = _export_stems(
            output_dir, shepherd_audio, swarm_audio, bed_audio, sr
        )
        paths["stems"] = stems_paths

    # Metadata
    effective_seed = seed if seed is not None else 0
    metadata = create_render_metadata(
        seed=effective_seed,
        duration_sec=effective_length_sec,
        sr=sr,
        voices={"shepherd": voice, "swarm": swarm_voice},
        epoch_boundaries=EPOCH_BOUNDARIES,
    )
    metadata_path = os.path.join(output_dir, "render.json")
    write_metadata(metadata_path, metadata)
    paths["metadata"] = metadata_path

    _report_progress(progress_callback, _PROGRESS_DONE, "Done!")

    return {"paths": paths, "metadata": metadata}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _report_progress(
    callback: ProgressCallback | None,
    fraction: float,
    description: str,
) -> None:
    """Invoke progress callback if provided."""
    if callback is not None:
        callback(fraction, description)


def _determine_length(
    shepherd_audio: np.ndarray,
    sr: int,
    requested_length_sec: int | None,
) -> int:
    """Determine effective session length in seconds.

    If requested_length_sec is provided, use it. Otherwise derive from
    shepherd audio length with a minimum of 60 seconds.
    """
    if requested_length_sec is not None:
        return requested_length_sec

    shepherd_length_sec = shepherd_audio.shape[0] // sr
    return max(shepherd_length_sec, 60)


def _render_shepherd(
    segments: list[dict[str, Any]],
    voice: str,
    target_sr: int,
    *,
    rng: np.random.Generator | None = None,
    progress_callback: ProgressCallback | None = None,
    progress_offset: float = 0.0,
    progress_scale: float = 1.0,
) -> np.ndarray:
    """Render the shepherd (main narration) audio track.

    Processes each segment: text → TTS, command → TTS + analog marking,
    pause → silence, snap → boundary event, drop_cue → word + snap.

    Returns stereo (N, 2) array at target_sr.
    """
    from hypnogen.core.epochs import generate_boundary_event

    tts_sr = TTS_SAMPLE_RATE
    mono_parts: list[np.ndarray] = []

    tts_segments = [
        s for s in segments if s["type"] in ("text", "command", "drop_cue")
    ]
    total_tts = len(tts_segments)
    tts_done = 0

    for segment in segments:
        seg_type = segment["type"]

        if seg_type == "text":
            audio, _ = synthesize(segment["text"], voice=voice, speed=0.9)
            mono_parts.append(audio)
            tts_done += 1
            _report_shepherd_progress(
                progress_callback, progress_offset, progress_scale,
                tts_done, total_tts,
            )

        elif seg_type == "command":
            audio, _ = synthesize(segment["text"], voice=voice, speed=0.9)
            pitch = segment.get("pitch", 0.0)
            rate = segment.get("rate", 1.0)
            if pitch != 0.0 or rate != 1.0:
                audio = apply_analog_marking(
                    audio, tts_sr, pitch_shift=pitch, rate=rate
                )
            mono_parts.append(audio)
            tts_done += 1
            _report_shepherd_progress(
                progress_callback, progress_offset, progress_scale,
                tts_done, total_tts,
            )

        elif seg_type == "pause":
            duration_ms = segment["duration_ms"]
            pause_samples = int((duration_ms / 1000) * tts_sr)
            mono_parts.append(np.zeros(pause_samples, dtype=np.float32))

        elif seg_type == "snap":
            snap_stereo = generate_boundary_event("snap", sr=tts_sr, rng=rng)
            mono_parts.append(snap_stereo[:, 0].astype(np.float32))

        elif seg_type == "drop_cue":
            word = segment.get("word", "drop")
            word_audio, _ = synthesize(word, voice=voice, speed=0.7)
            word_audio = apply_analog_marking(
                word_audio, tts_sr, pitch_shift=-3.0, rate=0.8
            )
            snap_stereo = generate_boundary_event("snap", sr=tts_sr, rng=rng)
            snap_mono = snap_stereo[:, 0]
            snap_padded = np.zeros_like(word_audio)
            snap_len = min(len(snap_mono), len(word_audio))
            snap_padded[:snap_len] = snap_mono[:snap_len] * 0.5
            combined = word_audio + snap_padded
            mono_parts.append(combined.astype(np.float32))
            tts_done += 1
            _report_shepherd_progress(
                progress_callback, progress_offset, progress_scale,
                tts_done, total_tts,
            )

    if not mono_parts:
        return np.zeros((1, 2), dtype=np.float32)

    mono_concat = np.concatenate(mono_parts)
    mono_resampled = _resample_if_needed(mono_concat, tts_sr, target_sr)
    return _to_stereo(mono_resampled)


def _report_shepherd_progress(
    callback: ProgressCallback | None,
    offset: float,
    scale: float,
    done: int,
    total: int,
) -> None:
    """Report shepherd TTS progress with segment counts."""
    if callback is not None and total > 0:
        frac = offset + (done / total) * scale
        callback(frac, f"Shepherd TTS: {done}/{total} segments")


def _render_swarm(
    affirmations: list[str],
    duration_sec: float,
    sr: int,
    voice: str,
    rng: np.random.Generator,
    *,
    progress_callback: ProgressCallback | None = None,
    progress_offset: float = 0.0,
    progress_scale: float = 1.0,
) -> np.ndarray:
    """Render the swarm (subliminal affirmations) audio track.

    Returns stereo (N, 2) array at sr.
    """
    tts_sr = TTS_SAMPLE_RATE
    affirmation_audios = []
    total = len(affirmations)

    for i, aff in enumerate(affirmations):
        audio, _ = synthesize(aff, voice=voice, speed=1.3)
        affirmation_audios.append(audio)
        if progress_callback is not None and total > 0:
            frac = progress_offset + ((i + 1) / total) * progress_scale
            progress_callback(frac, f"Swarm TTS: {i + 1}/{total} affirmations")

    swarm_at_tts_sr = generate_swarm(
        affirmation_audios, duration_sec, sr=tts_sr, rng=rng
    )
    left = _resample_if_needed(swarm_at_tts_sr[:, 0], tts_sr, sr)
    right = _resample_if_needed(swarm_at_tts_sr[:, 1], tts_sr, sr)
    return np.column_stack([left, right])


def _export_stems(
    output_dir: str,
    shepherd: np.ndarray,
    swarm: np.ndarray,
    bed: np.ndarray,
    sr: int,
) -> dict[str, str]:
    """Write individual layer stems as WAV files.

    Returns dict mapping layer name to file path.
    """
    stems: dict[str, str] = {}
    layers = {"shepherd": shepherd, "swarm": swarm, "bed": bed}

    for name, audio in layers.items():
        path = os.path.join(output_dir, f"{name}.wav")
        write_wav(path, audio, sr)
        stems[name] = path

    return stems


def _resample_if_needed(
    audio: np.ndarray, orig_sr: int, target_sr: int
) -> np.ndarray:
    """Resample audio if sample rates differ."""
    if orig_sr == target_sr:
        return audio
    return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)


def _to_stereo(audio: np.ndarray) -> np.ndarray:
    """Convert mono audio to stereo by duplicating the channel."""
    if audio.ndim == 1:
        return np.column_stack([audio, audio])
    return audio


def _pad_or_trim(audio: np.ndarray, target_samples: int) -> np.ndarray:
    """Pad with silence or trim to target sample count."""
    current_samples = audio.shape[0]
    if current_samples == target_samples:
        return audio
    if current_samples < target_samples:
        padding = np.zeros(
            (target_samples - current_samples, 2), dtype=audio.dtype
        )
        return np.concatenate([audio, padding], axis=0)
    return audio[:target_samples]
