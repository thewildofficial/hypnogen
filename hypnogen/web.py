"""Gradio web UI for Hypnogen."""

import argparse
import os
import tempfile

import gradio as gr
import librosa
import numpy as np

from hypnogen.core import (
    AVAILABLE_MODELS,
    LLMError,
    generate_affirmations as llm_generate_affirmations,
    generate_boundary_event,
    generate_script as llm_generate_script,
    generate_swarm,
    list_voices,
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
OUTPUT_SAMPLE_RATE = 44100

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


def _render_shepherd(
    segments: list,
    voice: str,
    target_sr: int,
    rng: np.random.Generator | None = None,
    progress: gr.Progress | None = None,
    progress_offset: float = 0.0,
    progress_scale: float = 1.0,
) -> np.ndarray:
    audio_parts = []
    tts_segments = [s for s in segments if s["type"] in ("text", "command", "drop_cue")]
    total_tts = len(tts_segments)
    tts_done = 0

    for segment in segments:
        seg_type = segment["type"]

        if seg_type == "text":
            audio, tts_sr = synthesize(segment["text"], voice=voice, speed=0.9)
            audio = _resample_if_needed(audio, tts_sr, target_sr)
            audio_parts.append(_to_stereo(audio))
            tts_done += 1
            if progress and total_tts > 0:
                frac = progress_offset + (tts_done / total_tts) * progress_scale
                progress(frac, desc=f"Shepherd TTS: {tts_done}/{total_tts} segments")

        elif seg_type == "command":
            audio, tts_sr = synthesize(segment["text"], voice=voice, speed=0.9)
            pitch = segment.get("pitch", 0.0)
            rate = segment.get("rate", 1.0)

            if pitch != 0.0 or rate != 1.0:
                audio = apply_analog_marking(audio, tts_sr, pitch_shift=pitch, rate=rate)

            audio = _resample_if_needed(audio, tts_sr, target_sr)
            audio_parts.append(_to_stereo(audio))
            tts_done += 1
            if progress and total_tts > 0:
                frac = progress_offset + (tts_done / total_tts) * progress_scale
                progress(frac, desc=f"Shepherd TTS: {tts_done}/{total_tts} segments")

        elif seg_type == "pause":
            duration_ms = segment["duration_ms"]
            pause_samples = int((duration_ms / 1000) * target_sr)
            pause_audio = np.zeros((pause_samples, 2), dtype=np.float32)
            audio_parts.append(pause_audio)

        elif seg_type == "snap":
            snap_audio = generate_boundary_event("snap", sr=target_sr, rng=rng)
            audio_parts.append(snap_audio.astype(np.float32))

        elif seg_type == "drop_cue":
            word = segment.get("word", "drop")
            word_audio, tts_sr = synthesize(word, voice=voice, speed=0.7)
            word_audio = apply_analog_marking(word_audio, tts_sr, pitch_shift=-3.0, rate=0.8)
            word_audio = _resample_if_needed(word_audio, tts_sr, target_sr)
            word_stereo = _to_stereo(word_audio)
            snap_audio = generate_boundary_event("snap", sr=target_sr, rng=rng)
            snap_padded = np.zeros_like(word_stereo)
            snap_len = min(snap_audio.shape[0], word_stereo.shape[0])
            snap_padded[:snap_len] = snap_audio[:snap_len] * 0.5
            combined = word_stereo + snap_padded
            audio_parts.append(combined.astype(np.float32))
            tts_done += 1
            if progress and total_tts > 0:
                frac = progress_offset + (tts_done / total_tts) * progress_scale
                progress(frac, desc=f"Shepherd TTS: {tts_done}/{total_tts} segments")

    if not audio_parts:
        return np.zeros((1, 2), dtype=np.float32)

    return np.concatenate(audio_parts, axis=0)


def _render_swarm(
    affirmations: list[str],
    duration_sec: float,
    sr: int,
    voice: str,
    rng: np.random.Generator,
    progress: gr.Progress | None = None,
    progress_offset: float = 0.0,
    progress_scale: float = 1.0,
) -> np.ndarray:
    affirmation_audios = []
    total = len(affirmations)
    for i, aff in enumerate(affirmations):
        audio, tts_sr = synthesize(aff, voice=voice, speed=1.3)
        audio = _resample_if_needed(audio, tts_sr, sr)
        affirmation_audios.append(audio)
        if progress and total > 0:
            frac = progress_offset + ((i + 1) / total) * progress_scale
            progress(frac, desc=f"Swarm TTS: {i + 1}/{total} affirmations")

    return generate_swarm(affirmation_audios, duration_sec, sr=sr, rng=rng)


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


def ai_generate_affirmations(goal: str, count: int = 20) -> str:
    if not goal or not goal.strip():
        raise gr.Error("Please enter a goal for affirmation generation")
    try:
        affirmations = llm_generate_affirmations(
            goal=goal.strip(),
            count=int(count),
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
    progress: gr.Progress = gr.Progress(),
) -> tuple[tuple[int, np.ndarray], str, str]:
    sr = OUTPUT_SAMPLE_RATE
    
    seed_val = int(seed) if seed is not None else None
    rng = np.random.default_rng(seed_val)
    
    voices = list_voices()
    if randomize_voices and len(voices) >= 2:
        chosen = rng.choice(voices, size=2, replace=False)
        shepherd_voice = chosen[0]
        swarm_voice = chosen[1]
    
    progress(0, desc="Parsing script...")
    segments = parse_script(script_text)
    valid, msg = validate_marking_density(segments)
    
    lines = [line.strip() for line in affirmations_text.splitlines() if line.strip()]
    valid_affirmations = []
    for line in lines:
        is_valid, _ = validate_affirmation(line)
        if is_valid:
            valid_affirmations.append(line)
    
    if not valid_affirmations:
        valid_affirmations = ["I am calm"]
    
    shepherd_audio = _render_shepherd(
        segments, shepherd_voice, sr, rng=rng,
        progress=progress, progress_offset=0.0, progress_scale=0.6,
    )
    length_sec = shepherd_audio.shape[0] // sr
    
    if length_sec < 60:
        min_samples = 60 * sr
        shepherd_audio = _pad_or_trim(shepherd_audio, min_samples)
        length_sec = 60
    
    swarm_audio = _render_swarm(
        valid_affirmations, length_sec, sr, swarm_voice, rng,
        progress=progress, progress_offset=0.6, progress_scale=0.3,
    )

    progress(0.9, desc="Generating binaural bed...")
    bed_audio = generate_bed(duration_sec=length_sec, sr=sr, rng=rng)
    
    target_samples = length_sec * sr
    shepherd_audio = _pad_or_trim(shepherd_audio, target_samples)
    swarm_audio = _pad_or_trim(swarm_audio, target_samples)
    bed_audio = _pad_or_trim(bed_audio, target_samples)
    
    progress(0.95, desc="Mixing layers & applying epochs...")
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
    
    progress(0.98, desc="Exporting WAV...")
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"hypnogen_{seed_val or 'random'}.wav")
    write_wav(temp_path, mixed, sr)
    
    audio_mono = np.mean(mixed, axis=1) if mixed.ndim == 2 else mixed
    
    progress(1.0, desc="Done!")
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
            inputs=[goal_input, aff_count_input],
            outputs=[affirmations_input],
        )
        gen_both_btn.click(
            fn=ai_generate_both,
            inputs=[
                goal_input, style_input, aff_count_input,
                duration_input, depth_input, density_input,
                focus_input, custom_instructions_input, model_dropdown,
            ],
            outputs=[script_input, affirmations_input],
        )
        generate_btn.click(
            fn=generate_audio,
            inputs=[script_input, affirmations_input, shepherd_voice_dropdown, swarm_voice_dropdown, randomize_voices_checkbox, seed_number],
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
