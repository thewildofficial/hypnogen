"""Full-pipeline CLI for hypnosis audio generation."""

import os

import click
import librosa
import numpy as np

from hypnogen.core import (
    EPOCH_BOUNDARIES,
    LLMError,
    create_render_metadata,
    export_session,
    generate_affirmations as llm_generate_affirmations,
    generate_script as llm_generate_script,
    generate_swarm,
    mix_layers,
    parse_script,
    select_boundary_events,
    validate_affirmation,
    validate_marking_density,
    write_wav,
)
from hypnogen.core.binaural import generate_bed
from hypnogen.core.effects import apply_analog_marking
from hypnogen.core.tts import synthesize


TTS_SAMPLE_RATE = 24000


@click.group()
def cli():
    """Hypnogen: Personalized hypnosis audio generator."""
    pass


@cli.command()
@click.option(
    "--script",
    "-s",
    type=click.Path(exists=True),
    default=None,
    help="Path to script file with embedded commands",
)
@click.option(
    "--affirmations",
    "-a",
    type=click.Path(exists=True),
    default=None,
    help="Path to affirmations file (one per line)",
)
@click.option(
    "--out",
    "-o",
    required=True,
    type=click.Path(),
    help="Output WAV file path",
)
@click.option(
    "--length-sec",
    "-l",
    default=600,
    type=int,
    help="Session length in seconds (default: 600)",
)
@click.option(
    "--seed",
    type=int,
    default=None,
    help="Random seed for reproducibility",
)
@click.option(
    "--voice",
    "-v",
    default="af_heart",
    help="TTS voice (default: af_heart)",
)
@click.option(
    "--stems-dir",
    type=click.Path(),
    help="Directory to export individual stems (optional)",
)
@click.option(
    "--sr",
    default=44100,
    type=int,
    help="Sample rate (default: 44100)",
)
@click.option(
    "--generate-script",
    is_flag=True,
    default=False,
    help="Generate script using LLM instead of reading from file",
)
@click.option(
    "--generate-affirmations",
    is_flag=True,
    default=False,
    help="Generate affirmations using LLM instead of reading from file",
)
@click.option(
    "--use-llm",
    is_flag=True,
    default=False,
    help="Generate both script and affirmations using LLM (shorthand for --generate-script --generate-affirmations)",
)
@click.option(
    "--goal",
    "-g",
    type=str,
    default=None,
    help="Goal for LLM generation (e.g., 'build confidence', 'sleep better')",
)
@click.option(
    "--style",
    type=str,
    default="ericksonian",
    help="Hypnosis script style for LLM (default: ericksonian)",
)
@click.option(
    "--affirmation-count",
    type=int,
    default=20,
    help="Number of affirmations to generate via LLM (default: 20)",
)
def generate(
    script,
    affirmations,
    out,
    length_sec,
    seed,
    voice,
    stems_dir,
    sr,
    generate_script,
    generate_affirmations,
    use_llm,
    goal,
    style,
    affirmation_count,
):
    """Generate hypnosis audio from script and affirmations.

    Provide script/affirmations via files (--script, --affirmations) or
    generate them with an LLM (--use-llm --goal "your goal").
    """
    # --use-llm is shorthand for both --generate-script and --generate-affirmations
    if use_llm:
        generate_script = True
        generate_affirmations = True

    # Validate: if using LLM generation, --goal is required
    if (generate_script or generate_affirmations) and not goal:
        click.echo("Error: --goal is required when using --generate-script, --generate-affirmations, or --use-llm", err=True)
        raise SystemExit(1)

    # Validate: must have a source for script and affirmations
    if not generate_script and not script:
        click.echo("Error: Either --script or --generate-script/--use-llm is required", err=True)
        raise SystemExit(1)
    if not generate_affirmations and not affirmations:
        click.echo("Error: Either --affirmations or --generate-affirmations/--use-llm is required", err=True)
        raise SystemExit(1)

    rng = np.random.default_rng(seed)

    # --- Script ---
    if generate_script:
        click.echo(f"Generating script with LLM for goal: {goal!r}...")
        try:
            script_text = llm_generate_script(
                goal=goal,
                duration_minutes=length_sec // 60,
                style=style,
            )
        except LLMError as e:
            click.echo(f"Error: LLM script generation failed: {e}", err=True)
            raise SystemExit(1)
        click.echo("Script generated successfully.")
    else:
        with open(script) as f:
            script_text = f.read()

    segments = parse_script(script_text)

    valid, msg = validate_marking_density(segments)
    if not valid:
        click.echo(f"Warning: {msg}", err=True)

    # --- Affirmations ---
    if generate_affirmations:
        click.echo(f"Generating {affirmation_count} affirmations with LLM for goal: {goal!r}...")
        try:
            valid_affirmations = llm_generate_affirmations(
                goal=goal,
                count=affirmation_count,
            )
        except LLMError as e:
            click.echo(f"Error: LLM affirmation generation failed: {e}", err=True)
            raise SystemExit(1)
        click.echo(f"Generated {len(valid_affirmations)} valid affirmations.")
    else:
        with open(affirmations) as f:
            lines = [line.strip() for line in f if line.strip()]

        valid_affirmations = []
        for line in lines:
            is_valid, reason = validate_affirmation(line)
            if is_valid:
                valid_affirmations.append(line)
            else:
                click.echo(f"Skipping affirmation: {line!r} ({reason})", err=True)

    if not valid_affirmations:
        click.echo("Error: No valid affirmations found", err=True)
        raise SystemExit(1)

    shepherd_audio = _render_shepherd(segments, voice, sr)
    swarm_audio = _render_swarm(valid_affirmations, length_sec, sr, voice, rng)
    bed_audio = generate_bed(duration_sec=length_sec, sr=sr, rng=rng)

    target_samples = length_sec * sr
    shepherd_audio = _pad_or_trim(shepherd_audio, target_samples)
    swarm_audio = _pad_or_trim(swarm_audio, target_samples)
    bed_audio = _pad_or_trim(bed_audio, target_samples)

    boundary_events = select_boundary_events(rng)
    mixed = mix_layers(
        shepherd=shepherd_audio,
        swarm=swarm_audio,
        bed=bed_audio,
        sr=sr,
        apply_epochs=True,
        boundary_events=boundary_events,
        rng=rng,
    )

    if stems_dir:
        metadata = create_render_metadata(
            seed=seed or 0,
            duration_sec=length_sec,
            sr=sr,
            voices={"shepherd": voice, "swarm": voice},
            epoch_boundaries=EPOCH_BOUNDARIES,
        )
        export_session(
            output_dir=stems_dir,
            metadata=metadata,
            shepherd=shepherd_audio,
            swarm=swarm_audio,
            bed=bed_audio,
            mix=mixed,
            sr=sr,
        )

    write_wav(out, mixed, sr)
    click.echo(f"Generated: {out}")


def _render_shepherd(segments: list, voice: str, target_sr: int) -> np.ndarray:
    audio_parts = []

    for segment in segments:
        seg_type = segment["type"]

        if seg_type == "text":
            audio, tts_sr = synthesize(segment["text"], voice=voice, speed=0.9)
            audio = _resample_if_needed(audio, tts_sr, target_sr)
            audio_parts.append(_to_stereo(audio))

        elif seg_type == "command":
            audio, tts_sr = synthesize(segment["text"], voice=voice, speed=0.9)
            pitch = segment.get("pitch", 0.0)
            rate = segment.get("rate", 1.0)

            if pitch != 0.0 or rate != 1.0:
                audio = apply_analog_marking(audio, tts_sr, pitch_shift=pitch, rate=rate)

            audio = _resample_if_needed(audio, tts_sr, target_sr)
            audio_parts.append(_to_stereo(audio))

        elif seg_type == "pause":
            duration_ms = segment["duration_ms"]
            pause_samples = int((duration_ms / 1000) * target_sr)
            pause_audio = np.zeros((pause_samples, 2), dtype=np.float32)
            audio_parts.append(pause_audio)

    if not audio_parts:
        return np.zeros((1, 2), dtype=np.float32)

    return np.concatenate(audio_parts, axis=0)


def _render_swarm(
    affirmations: list[str],
    duration_sec: float,
    sr: int,
    voice: str,
    rng: np.random.Generator,
) -> np.ndarray:
    affirmation_audios = []
    for aff in affirmations:
        audio, tts_sr = synthesize(aff, voice=voice, speed=1.3)
        audio = _resample_if_needed(audio, tts_sr, sr)
        affirmation_audios.append(audio)

    return generate_swarm(affirmation_audios, duration_sec, sr=sr, rng=rng)


def _resample_if_needed(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return audio
    return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)


def _to_stereo(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return np.column_stack([audio, audio])
    return audio


def _pad_or_trim(audio: np.ndarray, target_samples: int) -> np.ndarray:
    current_samples = audio.shape[0]

    if current_samples == target_samples:
        return audio

    if current_samples < target_samples:
        padding = np.zeros((target_samples - current_samples, 2), dtype=audio.dtype)
        return np.concatenate([audio, padding], axis=0)

    return audio[:target_samples]


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
