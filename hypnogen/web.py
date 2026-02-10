"""Gradio web UI for Hypnogen."""

import argparse
import os
import tempfile
import time

import gradio as gr
import numpy as np
import soundfile as sf

from hypnogen.core import (
    AVAILABLE_MODELS,
    LLMError,
    apply_gain_db,
    apply_limiter,
    generate_affirmations as llm_generate_affirmations,
    generate_script as llm_generate_script,
    list_voices,
    render_session,
    validate_affirmation,
    write_wav,
)
from hypnogen.core.binaural import generate_bed
from hypnogen.core.tts import synthesize


TTS_SAMPLE_RATE = 24000
OUTPUT_SAMPLE_RATE = 44100
CALIBRATION_SAMPLE_DURATION_SEC = 5

CALIBRATION_LEVELS = [
    (-30, "Very subtle - barely perceptible"),
    (-24, "Subtle - quiet background"),
    (-18, "Balanced - optimal for most (DEFAULT)"),
    (-12, "Audible - clearly hear words"),
    (-6, "Clear - very audible"),
]

DEFAULT_SUBLIMINAL_LEVEL_DB = -18.0

TONE_OPTIONS = [
    "calm therapeutic",
    "intense coach",
    "mystic-poetic",
    "clinical-precision",
    "minimalist",
]

DEFAULT_SCRIPT = """And now... as you <cmd pitch="-2" rate="0.9">relax deeply</cmd>... 
I want you to notice how your breathing... naturally slows down...

<pause duration="500ms"/>

With each breath... you can <cmd>feel more calm</cmd>... and at ease...
Allowing yourself to drift... deeper and deeper... into a peaceful state..."""

DEFAULT_AFFIRMATIONS = """I am confident
I am calm
I succeed easily
I am focused
I choose peace
My mind is clear
I am powerful"""


def _resample_if_needed(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Resample audio if sample rates differ. Used only by calibration."""
    import librosa
    if orig_sr == target_sr:
        return audio
    return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)


def _to_stereo(audio: np.ndarray) -> np.ndarray:
    """Convert mono to stereo. Used only by calibration."""
    if audio.ndim == 1:
        return np.column_stack([audio, audio])
    return audio


def _pad_or_trim(audio: np.ndarray, target_samples: int) -> np.ndarray:
    """Pad or trim stereo audio to target sample count. Used only by calibration."""
    current_samples = audio.shape[0]
    if current_samples == target_samples:
        return audio
    if current_samples < target_samples:
        padding = np.zeros((target_samples - current_samples, 2), dtype=audio.dtype)
        return np.concatenate([audio, padding], axis=0)
    return audio[:target_samples]


def generate_calibration_samples(voice: str) -> list[str]:
    """Generate 5 calibration audio samples at different subliminal levels.

    Each sample is ~5 seconds of a test affirmation mixed over a pink noise bed
    at a different swarm gain level. Returns file paths to temporary WAV files.

    Args:
        voice: Voice ID for TTS synthesis.

    Returns:
        List of 5 file paths to temporary WAV files, one per calibration level.
    """
    sr = OUTPUT_SAMPLE_RATE
    duration_samples = CALIBRATION_SAMPLE_DURATION_SEC * sr
    calibration_text = "I am calm and confident"
    rng = np.random.default_rng(0)

    # Synthesize the test affirmation once
    tts_audio, tts_sr = synthesize(calibration_text, voice=voice, speed=1.0)
    tts_audio = _resample_if_needed(tts_audio, tts_sr, sr)

    # Generate pink noise bed for the calibration duration
    bed_audio = generate_bed(duration_sec=CALIBRATION_SAMPLE_DURATION_SEC, sr=sr, rng=rng)
    bed_audio = _pad_or_trim(bed_audio, duration_samples)

    # Build a simple swarm-like layer: repeat the affirmation with some gaps
    swarm_mono = np.zeros(duration_samples, dtype=np.float32)
    # Place affirmation at 0.5s and 3.0s for two repetitions
    placement_offsets = [int(0.5 * sr), int(3.0 * sr)]
    for offset in placement_offsets:
        end = min(offset + len(tts_audio), duration_samples)
        clip_len = end - offset
        if clip_len > 0:
            swarm_mono[offset:end] += tts_audio[:clip_len]

    swarm_stereo = _to_stereo(swarm_mono)

    # Apply bed gain (constant across all samples)
    bed_gained = apply_gain_db(bed_audio, -12.0)

    sample_paths = []
    for level_db, _desc in CALIBRATION_LEVELS:
        # Apply swarm gain at this calibration level
        swarm_gained = apply_gain_db(swarm_stereo, float(level_db))

        # Mix bed + swarm
        mixed = bed_gained.astype(np.float64) + swarm_gained.astype(np.float64)
        mixed = mixed.astype(np.float32)

        # Limit to prevent clipping
        mixed = apply_limiter(mixed, sr, threshold_db=-1.0)

        # Write to temp file
        temp_path = os.path.join(
            tempfile.gettempdir(),
            f"hypnogen_cal_{level_db}dB.wav",
        )
        write_wav(temp_path, mixed, sr)
        sample_paths.append(temp_path)

    return sample_paths


def _map_model_display_to_id(display_name: str) -> str:
    for display, model_id in AVAILABLE_MODELS:
        if display == display_name:
            return model_id
    return "gemini-pro"


def ai_generate_script(
    goal: str,
    style: str,
    duration_minutes: float,
    depth: str,
    command_density: str,
    focus_theme: str,
    custom_instructions: str,
    model: str,
) -> str:
    if not goal or not goal.strip():
        raise gr.Error("Please enter a goal for script generation")
    try:
        model_id = _map_model_display_to_id(model)
        script = llm_generate_script(
            goal=goal.strip(),
            duration_minutes=int(duration_minutes) if duration_minutes else 10,
            style=style or "ericksonian",
            depth=depth or "medium",
            command_density=command_density or "medium",
            focus_theme=focus_theme.strip() if focus_theme else "",
            custom_instructions=custom_instructions.strip() if custom_instructions else "",
            model=model_id,
        )
        return script
    except LLMError as e:
        raise gr.Error(f"LLM script generation failed: {e}")


def ai_generate_affirmations(goal: str, count: int = 20, tone: str = "calm therapeutic") -> str:
    if not goal or not goal.strip():
        raise gr.Error("Please enter a goal for affirmation generation")
    try:
        affirmations = llm_generate_affirmations(
            goal=goal.strip(),
            count=int(count),
            tone=tone,
        )
        return "\n".join(affirmations)
    except LLMError as e:
        raise gr.Error(f"LLM affirmation generation failed: {e}")


def ai_generate_both(
    goal: str,
    style: str,
    count: int,
    duration_minutes: float,
    depth: str,
    command_density: str,
    focus_theme: str,
    custom_instructions: str,
    model: str,
    tone: str = "calm therapeutic",
) -> tuple[str, str]:
    if not goal or not goal.strip():
        raise gr.Error("Please enter a goal for generation")
    try:
        script = llm_generate_script(
            goal=goal.strip(),
            duration_minutes=int(duration_minutes) if duration_minutes else 10,
            style=style or "ericksonian",
            depth=depth or "medium",
            command_density=command_density or "medium",
            focus_theme=focus_theme.strip() if focus_theme else "",
            custom_instructions=custom_instructions.strip() if custom_instructions else "",
        )
        affirmations = llm_generate_affirmations(
            goal=goal.strip(),
            count=int(count),
            tone=tone,
        )
        return script, "\n".join(affirmations)
    except LLMError as e:
        raise gr.Error(f"LLM generation failed: {e}")


def generate_audio(
    script_text: str,
    affirmations_text: str,
    shepherd_voice: str,
    swarm_voice: str,
    randomize_voices: bool,
    seed: int | None,
    subliminal_level_db: float = DEFAULT_SUBLIMINAL_LEVEL_DB,
    progress: gr.Progress = gr.Progress(),
) -> tuple[tuple[int, np.ndarray], str, str]:
    sr = OUTPUT_SAMPLE_RATE

    seed_val = int(seed) if seed is not None else None

    # Voice randomization is a UI concern — handle before delegating
    if randomize_voices:
        voices = list_voices()
        if len(voices) >= 2:
            rng_voices = np.random.default_rng(seed_val)
            chosen = rng_voices.choice(voices, size=2, replace=False)
            shepherd_voice = chosen[0]
            swarm_voice = chosen[1]

    # Validate affirmations (UI concern — user feedback)
    lines = [line.strip() for line in affirmations_text.splitlines() if line.strip()]
    valid_affirmations = []
    for line in lines:
        is_valid, _ = validate_affirmation(line)
        if is_valid:
            valid_affirmations.append(line)

    if not valid_affirmations:
        valid_affirmations = ["I am calm"]

    # Adapt gr.Progress to render_session's progress_callback protocol
    def _progress_adapter(fraction: float, description: str) -> None:
        progress(fraction, desc=description)
        time.sleep(0)

    # Delegate to render-core
    with tempfile.TemporaryDirectory() as render_dir:
        result = render_session(
            script_text=script_text,
            affirmations=valid_affirmations,
            output_dir=render_dir,
            voice=shepherd_voice,
            swarm_voice=swarm_voice,
            seed=seed_val,
            length_sec=None,  # Derive from shepherd audio
            sr=sr,
            gain_db={"swarm": subliminal_level_db},
            progress_callback=_progress_adapter,
        )

        # Read back the mix WAV for Gradio playback
        mix_path = result["paths"]["mix"]
        mixed, _ = sf.read(mix_path, dtype="float32")

        # Copy to a stable temp location for download
        temp_path = os.path.join(
            tempfile.gettempdir(),
            f"hypnogen_{seed_val or 'random'}.wav",
        )
        write_wav(temp_path, mixed, sr)

    audio_mono = np.mean(mixed, axis=1) if mixed.ndim == 2 else mixed
    length_sec = result["metadata"]["duration_sec"]
    info_text = f"Generated {length_sec}s session | Shepherd voice: {shepherd_voice} | Swarm voice: {swarm_voice}"

    return (sr, audio_mono), temp_path, info_text


def create_ui() -> gr.Blocks:
    with gr.Blocks(title="Hypnogen") as app:
        gr.Markdown("# Hypnogen: Personalized Hypnosis Audio Generator")
        gr.Markdown("Generate multi-layer hypnosis tracks with Ericksonian induction, embedded commands, and subliminal affirmations.")
        
        with gr.Accordion("Generate with AI", open=False):
            gr.Markdown("Use an LLM to generate scripts and affirmations from a goal.")
            with gr.Row():
                goal_input = gr.Textbox(
                    label="Goal",
                    placeholder="e.g., build confidence, sleep better, overcome anxiety",
                    lines=1,
                    scale=3,
                )
                model_dropdown = gr.Dropdown(
                    choices=[m[0] for m in AVAILABLE_MODELS],
                    value=AVAILABLE_MODELS[0][0],
                    label="AI Model",
                    scale=1,
                )
            with gr.Row():
                style_input = gr.Dropdown(
                    choices=["ericksonian", "permissive", "authoritative", "conversational", "fractionation"],
                    value="ericksonian",
                    label="Script Style",
                )
                depth_input = gr.Dropdown(
                    choices=["light", "medium", "deep", "somnambulistic"],
                    value="medium",
                    label="Induction Depth",
                )
                density_input = gr.Dropdown(
                    choices=["low", "medium", "high"],
                    value="medium",
                    label="Embedded Command Density",
                )
                duration_input = gr.Number(
                    value=10,
                    label="Target Duration (min)",
                    precision=0,
                    minimum=3,
                    maximum=60,
                )
                aff_count_input = gr.Number(
                    value=20,
                    label="Affirmation Count",
                    precision=0,
                )
                tone_dropdown = gr.Dropdown(
                    choices=TONE_OPTIONS,
                    value="calm therapeutic",
                    label="Affirmation Tone",
                )
            with gr.Row():
                focus_input = gr.Textbox(
                    label="Theme / Focus (optional)",
                    placeholder="e.g., public speaking, exam preparation, morning energy",
                    lines=1,
                    scale=1,
                )
            with gr.Row():
                custom_instructions_input = gr.Textbox(
                    label="Custom Instructions (optional)",
                    placeholder="e.g., Include a body scan, use ocean metaphors, mention my safe place...",
                    lines=2,
                    scale=1,
                )
            with gr.Row():
                gen_script_btn = gr.Button("Generate Script", variant="secondary")
                gen_aff_btn = gr.Button("Generate Affirmations", variant="secondary")
                gen_both_btn = gr.Button("Generate Both", variant="primary")

        with gr.Row():
            with gr.Column():
                script_input = gr.Textbox(
                    label="Hypnotic Script",
                    placeholder="Enter your script with <cmd>embedded commands</cmd>...",
                    value=DEFAULT_SCRIPT,
                    lines=10,
                )
                affirmations_input = gr.Textbox(
                    label="Affirmations (one per line)",
                    placeholder="I am confident\nI am calm\n...",
                    value=DEFAULT_AFFIRMATIONS,
                    lines=5,
                )
                gr.Markdown(
                    "**Disclaimer:** Hypnogen is for experimental purposes only. "
                    "Not intended for minors. Requires consent from anyone who may hear the audio."
                )
                
            with gr.Column():
                shepherd_voice_dropdown = gr.Dropdown(
                    choices=list_voices(),
                    value="af_heart",
                    label="Shepherd Voice (Main)",
                )
                swarm_voice_dropdown = gr.Dropdown(
                    choices=list_voices(),
                    value="af_heart",
                    label="Swarm Voice (Background)",
                )
                randomize_voices_checkbox = gr.Checkbox(
                    value=False,
                    label="Randomize voices (pick different voices for each track)",
                )
                seed_number = gr.Number(
                    value=None,
                    label="Random Seed (optional)",
                    precision=0,
                )
                duration_info = gr.Textbox(
                    label="Session Info",
                    value="Duration auto-calculated from script",
                    interactive=False,
                )
                
                with gr.Accordion("Subliminal Audibility Calibration", open=False) as calib_accordion:
                    gr.Markdown(
                        "Listen to each sample. Which level can you hear the words when focused, "
                        "but blends into background when not?"
                    )
                    calib_audios = []
                    for level, label in CALIBRATION_LEVELS:
                        calib_audios.append(gr.Audio(label=f"{label} ({level} dB)", interactive=False))
                    
                    calib_level = gr.Radio(
                        choices=[(f"{label} ({level} dB)", level) for level, label in CALIBRATION_LEVELS],
                        value=-18,
                        label="Selected Audibility Level",
                    )
                    gen_calib_btn = gr.Button("Generate Calibration Samples")

                generate_btn = gr.Button("Generate Audio", variant="primary")
        
        with gr.Row():
            audio_output = gr.Audio(label="Generated Audio", type="numpy")
            download_file = gr.File(label="Download WAV")
        
        gen_script_btn.click(
            fn=ai_generate_script,
            inputs=[
                goal_input, style_input, duration_input,
                depth_input, density_input, focus_input,
                custom_instructions_input, model_dropdown,
            ],
            outputs=[script_input],
        )
        gen_aff_btn.click(
            fn=ai_generate_affirmations,
            inputs=[goal_input, aff_count_input, tone_dropdown],
            outputs=[affirmations_input],
        )
        gen_both_btn.click(
            fn=ai_generate_both,
            inputs=[
                goal_input, style_input, aff_count_input,
                duration_input, depth_input, density_input,
                focus_input, custom_instructions_input, model_dropdown,
                tone_dropdown,
            ],
            outputs=[script_input, affirmations_input],
        )
        
        gen_calib_btn.click(
            fn=generate_calibration_samples,
            inputs=[swarm_voice_dropdown],
            outputs=calib_audios,
        )

        generate_btn.click(
            fn=generate_audio,
            inputs=[
                script_input, affirmations_input, shepherd_voice_dropdown, 
                swarm_voice_dropdown, randomize_voices_checkbox, seed_number,
                calib_level
            ],
            outputs=[audio_output, download_file, duration_info],
        )
    
    return app


def main():
    """Entry point for web UI."""
    parser = argparse.ArgumentParser(description="Hypnogen Web UI")
    parser.add_argument("--port", type=int, default=7860, help="Port to serve on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()
    
    app = create_ui()
    app.launch(server_name=args.host, server_port=args.port)


if __name__ == "__main__":
    main()
