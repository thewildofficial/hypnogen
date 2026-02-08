"""Export module for stems I/O and render metadata JSON."""

from __future__ import annotations

import json
import os
from typing import Any

import numpy as np
import soundfile as sf


def write_wav(filepath: str, audio: np.ndarray, sr: int) -> None:
    """Write audio array to WAV file.
    
    Args:
        filepath: Output path (e.g., "output.wav")
        audio: Audio array, mono (N,) or stereo (N, 2)
        sr: Sample rate
    """
    sf.write(filepath, audio, sr, subtype="FLOAT")


def export_stems(
    stems_dir: str,
    shepherd: np.ndarray | None = None,
    weaver: np.ndarray | None = None,
    swarm: np.ndarray | None = None,
    bed: np.ndarray | None = None,
    mix: np.ndarray | None = None,
    sr: int = 44100,
) -> None:
    """Export all audio layers as separate WAV files.
    
    Args:
        stems_dir: Directory to write stems (created if doesn't exist)
        shepherd/weaver/swarm/bed: Individual layer audio arrays
        mix: Final mixed output
        sr: Sample rate
    """
    os.makedirs(stems_dir, exist_ok=True)
    
    stems = {
        "shepherd": shepherd,
        "weaver": weaver,
        "swarm": swarm,
        "bed": bed,
        "mix": mix,
    }
    
    for name, audio in stems.items():
        if audio is not None:
            filepath = os.path.join(stems_dir, f"{name}.wav")
            write_wav(filepath, audio, sr)


def create_render_metadata(
    seed: int,
    duration_sec: float,
    sr: int = 44100,
    voices: dict[str, str] | None = None,
    pitch_params: dict[str, float] | None = None,
    gain_staging: dict[str, float] | None = None,
    epoch_boundaries: tuple[float, ...] = (0.0, 0.2, 0.5, 0.85, 1.0),
    version: str = "0.1.0",
) -> dict[str, Any]:
    """Create render metadata for reproducibility.
    
    Returns:
        Dictionary with all parameters needed to reproduce the render.
    """
    return {
        "seed": seed,
        "sample_rate": sr,
        "duration_sec": duration_sec,
        "voices": voices,
        "pitch_params": pitch_params,
        "gain_staging": gain_staging,
        "epoch_boundaries": list(epoch_boundaries),
        "version": version,
    }


def write_metadata(filepath: str, metadata: dict[str, Any]) -> None:
    """Write render metadata to JSON file.
    
    Args:
        filepath: Output path (e.g., "render.json")
        metadata: Dictionary from create_render_metadata()
    """
    with open(filepath, "w") as f:
        json.dump(metadata, f, indent=2)


def export_session(
    output_dir: str,
    metadata: dict[str, Any],
    shepherd: np.ndarray | None = None,
    weaver: np.ndarray | None = None,
    swarm: np.ndarray | None = None,
    bed: np.ndarray | None = None,
    mix: np.ndarray | None = None,
    sr: int = 44100,
) -> None:
    """Export complete session: stems + metadata.
    
    Args:
        output_dir: Directory for all output files
        metadata: Render metadata dict
        shepherd/weaver/swarm/bed: Individual layer audio arrays
        mix: Final mixed output
        sr: Sample rate
    """
    os.makedirs(output_dir, exist_ok=True)
    
    export_stems(
        output_dir,
        shepherd=shepherd,
        weaver=weaver,
        swarm=swarm,
        bed=bed,
        mix=mix,
        sr=sr,
    )
    
    metadata_path = os.path.join(output_dir, "render.json")
    write_metadata(metadata_path, metadata)
