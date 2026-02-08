"""Gradio web UI for Hypnogen."""

import argparse
import os
import tempfile

import gradio as gr
import librosa
import numpy as np

from hypnogen.core import (
    LLMError,
    generate_affirmations as llm_generate_affirmations,
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


def ai_generate_script(goal: str, length_sec: int, style: str) -> str:
    if not goal or not goal.strip():
        raise gr.Error("Please enter a goal for script generation")
    try:
        script = llm_generate_script(
            goal=goal.strip(),
            duration_minutes=max(1, length_sec // 60),
            style=style or "ericksonian",
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


def generate_audio(
    script_text: str,
    affirmations_text: str,
    voice: str,
    length_sec: int,
    seed: int | None,
) -> tuple[tuple[int, np.ndarray], str]:
    """Generate audio from UI inputs.
    
    Returns:
        ((sample_rate, audio_array), filepath) for Gradio audio component and download.
    """
    sr = OUTPUT_SAMPLE_RATE
    
    seed_val = int(seed) if seed is not None else None
    rng = np.random.default_rng(seed_val)
    
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
    
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"hypnogen_{seed_val or 'random'}.wav")
    write_wav(temp_path, mixed, sr)
    
    audio_mono = np.mean(mixed, axis=1) if mixed.ndim == 2 else mixed
    
    return (sr, audio_mono), temp_path


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
                )
                style_input = gr.Dropdown(
                    choices=["ericksonian", "permissive", "authoritative", "conversational"],
                    value="ericksonian",
                    label="Script Style",
                )
                aff_count_input = gr.Number(
                    value=20,
                    label="Affirmation Count",
                    precision=0,
                )
            with gr.Row():
                gen_script_btn = gr.Button("Generate Script", variant="secondary")
                gen_aff_btn = gr.Button("Generate Affirmations", variant="secondary")

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
                voice_dropdown = gr.Dropdown(
                    choices=list_voices(),
                    value="af_heart",
                    label="Voice",
                )
                length_slider = gr.Slider(
                    minimum=60,
                    maximum=1800,
                    step=60,
                    value=600,
                    label="Length (seconds)",
                )
                seed_number = gr.Number(
                    value=None,
                    label="Random Seed (optional)",
                    precision=0,
                )
                generate_btn = gr.Button("Generate Audio", variant="primary")
        
        with gr.Row():
            audio_output = gr.Audio(label="Generated Audio", type="numpy")
            download_file = gr.File(label="Download WAV")
        
        gen_script_btn.click(
            fn=ai_generate_script,
            inputs=[goal_input, length_slider, style_input],
            outputs=[script_input],
        )
        gen_aff_btn.click(
            fn=ai_generate_affirmations,
            inputs=[goal_input, aff_count_input],
            outputs=[affirmations_input],
        )
        generate_btn.click(
            fn=generate_audio,
            inputs=[script_input, affirmations_input, voice_dropdown, length_slider, seed_number],
            outputs=[audio_output, download_file],
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
