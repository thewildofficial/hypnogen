"""Full-pipeline CLI for hypnosis audio generation."""

import os
import shutil
import tempfile

import click

from hypnogen.core import (
    LLMError,
    generate_affirmations as llm_generate_affirmations,
    generate_script as llm_generate_script,
    parse_script,
    render_session,
    validate_affirmation,
    validate_marking_density,
)


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

    # --- Render via render-core ---
    with tempfile.TemporaryDirectory() as render_dir:
        result = render_session(
            script_text=script_text,
            affirmations=valid_affirmations,
            output_dir=render_dir,
            voice=voice,
            seed=seed,
            length_sec=length_sec,
            sr=sr,
            export_stems=bool(stems_dir),
        )

        # Copy mix WAV to the user-specified output path
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        shutil.copy2(result["paths"]["mix"], out)

        # Copy stems to the user-specified stems directory if requested
        if stems_dir:
            os.makedirs(stems_dir, exist_ok=True)
            # Copy stem WAVs
            for stem_name, stem_path in result["paths"]["stems"].items():
                shutil.copy2(stem_path, os.path.join(stems_dir, f"{stem_name}.wav"))
            # Also copy the mix and render.json into stems dir
            shutil.copy2(result["paths"]["mix"], os.path.join(stems_dir, "mix.wav"))
            shutil.copy2(
                result["paths"]["metadata"],
                os.path.join(stems_dir, "render.json"),
            )

    click.echo(f"Generated: {out}")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
