"""Benchmark harness for the hypnogen render pipeline.

Runs a deterministic render with fixed fixtures and captures per-stage timings.
Results are written as JSON for regression tracking.

Usage:
    python -m hypnogen.benchmarks.bench_render \
        --out /tmp/bench.wav \
        --json .sisyphus/benchmarks/baseline.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

import librosa
import numpy as np

from hypnogen.core.binaural import generate_bed
from hypnogen.core.export import write_wav
from hypnogen.core.mixer import mix_layers
from hypnogen.core.parser import parse_script
from hypnogen.core.swarm import generate_swarm
from hypnogen.core.tts import synthesize
from hypnogen.core.epochs import select_boundary_events

# ---------------------------------------------------------------------------
# Deterministic fixtures
# ---------------------------------------------------------------------------

FIXTURE_SEED = 42

FIXTURE_VOICE = "af_heart"

FIXTURE_SCRIPT = (
    "Welcome to this moment of deep relaxation.\n"
    '<pause duration="500ms"/>\n'
    "Allow your eyes to gently close as you begin to unwind.\n"
    '<cmd pitch="-2">Let go of all tension now.</cmd>\n'
    '<pause duration="300ms"/>\n'
    "With each breath, you sink deeper into comfort and calm.\n"
)

FIXTURE_AFFIRMATIONS = [
    "I am calm and centered",
    "I feel safe and at peace",
    "I embrace this moment fully",
]

FIXTURE_LENGTH_SEC = 10
FIXTURE_SR = 44100
TTS_SAMPLE_RATE = 24000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_git_sha() -> str:
    """Return short git SHA or 'unknown' if not in a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def _compute_config_hash() -> str:
    """Deterministic hash of the fixture configuration."""
    config_str = json.dumps(
        {
            "script": FIXTURE_SCRIPT,
            "affirmations": FIXTURE_AFFIRMATIONS,
            "voice": FIXTURE_VOICE,
            "seed": FIXTURE_SEED,
            "length_sec": FIXTURE_LENGTH_SEC,
            "sr": FIXTURE_SR,
        },
        sort_keys=True,
    )
    return hashlib.sha256(config_str.encode()).hexdigest()[:12]


def _resample_if_needed(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return audio
    return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)


def _to_stereo(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return np.column_stack([audio, audio])
    return audio


def _pad_or_trim(audio: np.ndarray, target_samples: int) -> np.ndarray:
    current = audio.shape[0]
    if current == target_samples:
        return audio
    if current < target_samples:
        padding = np.zeros((target_samples - current, 2), dtype=audio.dtype)
        return np.concatenate([audio, padding], axis=0)
    return audio[:target_samples]


# ---------------------------------------------------------------------------
# Stage runners (each returns (result, elapsed_seconds))
# ---------------------------------------------------------------------------

def _stage_parse() -> tuple[list, float]:
    t0 = time.perf_counter()
    segments = parse_script(FIXTURE_SCRIPT)
    elapsed = time.perf_counter() - t0
    return segments, elapsed


def _stage_tts(segments: list, rng: np.random.Generator) -> tuple[tuple[np.ndarray, np.ndarray], float]:
    """Run TTS for shepherd + swarm, return (shepherd_stereo, swarm_stereo) and elapsed time."""
    from hypnogen.core.effects import apply_analog_marking

    t0 = time.perf_counter()

    # --- Shepherd TTS ---
    tts_sr = TTS_SAMPLE_RATE
    mono_parts: list[np.ndarray] = []
    for segment in segments:
        seg_type = segment["type"]
        if seg_type == "text":
            audio, _ = synthesize(segment["text"], voice=FIXTURE_VOICE, speed=0.9)
            mono_parts.append(audio)
        elif seg_type == "command":
            audio, _ = synthesize(segment["text"], voice=FIXTURE_VOICE, speed=0.9)
            pitch = segment.get("pitch", 0.0)
            rate = segment.get("rate", 1.0)
            if pitch != 0.0 or rate != 1.0:
                audio = apply_analog_marking(audio, tts_sr, pitch_shift=pitch, rate=rate)
            mono_parts.append(audio)
        elif seg_type == "pause":
            pause_samples = int((segment["duration_ms"] / 1000) * tts_sr)
            mono_parts.append(np.zeros(pause_samples, dtype=np.float32))

    if mono_parts:
        shepherd_mono = np.concatenate(mono_parts)
    else:
        shepherd_mono = np.zeros(1, dtype=np.float32)
    shepherd_resampled = _resample_if_needed(shepherd_mono, tts_sr, FIXTURE_SR)
    shepherd_stereo = _to_stereo(shepherd_resampled)

    # --- Swarm TTS ---
    affirmation_audios = []
    for aff in FIXTURE_AFFIRMATIONS:
        audio, _ = synthesize(aff, voice=FIXTURE_VOICE, speed=1.3)
        affirmation_audios.append(audio)
    swarm_at_tts_sr = generate_swarm(affirmation_audios, FIXTURE_LENGTH_SEC, sr=tts_sr, rng=rng)
    left = _resample_if_needed(swarm_at_tts_sr[:, 0], tts_sr, FIXTURE_SR)
    right = _resample_if_needed(swarm_at_tts_sr[:, 1], tts_sr, FIXTURE_SR)
    swarm_stereo = np.column_stack([left, right])

    elapsed = time.perf_counter() - t0
    return (shepherd_stereo, swarm_stereo), elapsed


def _stage_mix(
    shepherd: np.ndarray,
    swarm: np.ndarray,
    bed: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, float]:
    target_samples = FIXTURE_LENGTH_SEC * FIXTURE_SR
    shepherd = _pad_or_trim(shepherd, target_samples)
    swarm = _pad_or_trim(swarm, target_samples)
    bed = _pad_or_trim(bed, target_samples)

    t0 = time.perf_counter()
    boundary_events = select_boundary_events(rng)
    mixed = mix_layers(
        shepherd=shepherd,
        swarm=swarm,
        bed=bed,
        sr=FIXTURE_SR,
        apply_epochs=True,
        boundary_events=boundary_events,
        rng=rng,
    )
    elapsed = time.perf_counter() - t0
    return mixed, elapsed


def _stage_export(mixed: np.ndarray, out_path: str) -> float:
    t0 = time.perf_counter()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    write_wav(out_path, mixed, FIXTURE_SR)
    elapsed = time.perf_counter() - t0
    return elapsed


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_benchmark(
    out_path: str,
    json_path: str | None = None,
) -> dict[str, Any]:
    """Run the full benchmark and return results.

    Args:
        out_path: Where to write the rendered WAV.
        json_path: Optional path to write JSON results.

    Returns:
        Dict with total_sec, stages, config_hash, git_sha, timestamp.
    """
    rng = np.random.default_rng(FIXTURE_SEED)
    total_t0 = time.perf_counter()

    # 1. Parse
    segments, parse_time = _stage_parse()

    # 2. TTS (shepherd + swarm) + binaural bed generation
    (shepherd, swarm), tts_time = _stage_tts(segments, rng)
    bed = generate_bed(duration_sec=FIXTURE_LENGTH_SEC, sr=FIXTURE_SR, rng=rng)

    # 3. Mix
    mixed, mix_time = _stage_mix(shepherd, swarm, bed, rng)

    # 4. Export
    export_time = _stage_export(mixed, out_path)

    total_sec = time.perf_counter() - total_t0

    result: dict[str, Any] = {
        "total_sec": total_sec,
        "stages": {
            "parse": parse_time,
            "tts": tts_time,
            "mix": mix_time,
            "export": export_time,
        },
        "config_hash": _compute_config_hash(),
        "git_sha": _get_git_sha(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if json_path:
        os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(result, f, indent=2)

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run hypnogen render benchmark with fixed fixtures.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output WAV file path",
    )
    parser.add_argument(
        "--json",
        default=None,
        help="Path to write JSON results (optional)",
    )
    args = parser.parse_args()

    result = run_benchmark(out_path=args.out, json_path=args.json)

    print(f"Benchmark complete in {result['total_sec']:.3f}s")
    for stage, elapsed in result["stages"].items():
        print(f"  {stage:>8s}: {elapsed:.3f}s")
    print(f"  config: {result['config_hash']}")
    print(f"  git:    {result['git_sha']}")

    if args.json:
        print(f"  json:   {args.json}")


if __name__ == "__main__":
    main()
