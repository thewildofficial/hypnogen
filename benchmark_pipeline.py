#!/usr/bin/env python3
"""Stage-level benchmark harness for the Hypnogen render pipeline.

Profiles each pipeline stage independently using hardcoded script + affirmations
(no LLM API keys required). Outputs JSON results to .sisyphus/benchmarks/.

Usage:
    python benchmark_pipeline.py                # Default short run
    python benchmark_pipeline.py --scale large  # Longer script for realistic timing
    python benchmark_pipeline.py --warmup       # Warm up TTS model first
"""

import argparse
import json
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone

import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from hypnogen.core import (
    generate_swarm,
    mix_layers,
    parse_script,
    select_boundary_events,
    write_wav,
)
from hypnogen.core.binaural import generate_bed
from hypnogen.core.effects import apply_analog_marking
from hypnogen.core.tts import synthesize

# ─── Constants ───────────────────────────────────────────────────────────────

TTS_SAMPLE_RATE = 24000
OUTPUT_SAMPLE_RATE = 44100
BENCHMARKS_DIR = os.path.join(os.path.dirname(__file__), ".sisyphus", "benchmarks")

# Short script (~60s output) for quick profiling
SHORT_SCRIPT = """And now... as you <cmd pitch="-2" rate="0.9">relax deeply</cmd>...
I want you to notice how your breathing... naturally slows down...

<pause duration="500ms"/>

With each breath... you can <cmd>feel more calm</cmd>... and at ease...
Allowing yourself to drift... deeper and deeper... into a peaceful state...

<pause duration="1000ms"/>

And as you continue to relax... your body feels heavier...
Every muscle releasing tension... <cmd pitch="-1.5" rate="0.85">letting go completely</cmd>...

<snap/>

That's right... just let everything go now...
There is nothing you need to do... nowhere you need to be...

<pause duration="800ms"/>

Your mind can wander freely... peacefully...
Each thought that arises... simply floats away... like a cloud in the sky...
"""

# Large script (~15-18 min output) simulating real LLM-generated content
LARGE_SCRIPT = """Welcome... and as you settle in... I want you to take a slow... deep breath...
Let your body sink into wherever you are resting...

<pause duration="2000ms"/>

And now... as you <cmd pitch="-2" rate="0.9">begin to relax</cmd>...
notice how your breathing naturally starts to slow down...
Each inhale... brings calm... each exhale... releases tension...

<pause duration="1500ms"/>

That's right... and with every breath you take...
you can <cmd>feel yourself going deeper</cmd>... and deeper...
into a wonderful state of relaxation...

<pause duration="1000ms"/>

Now I want you to imagine... a warm golden light...
beginning at the top of your head...
This light is healing... soothing... and everywhere it touches...
the muscles simply <cmd pitch="-1.5" rate="0.85">melt and release</cmd>...

<snap/>

<pause duration="800ms"/>

Feel that warmth spreading down... across your forehead...
smoothing away any lines of tension...
Down through your temples... your jaw... <cmd>letting go completely</cmd>...

<pause duration="1200ms"/>

Your shoulders... which carry so much... can now rest...
Feel them dropping... releasing... becoming wonderfully heavy...

<pause duration="1000ms"/>

And as this warm light continues to flow downward...
through your arms... your hands... your fingertips...
you might notice a pleasant tingling sensation...
That's perfectly natural... it means you are <cmd pitch="-2" rate="0.9">going deeper now</cmd>...

<pause duration="1500ms"/>

Down through your chest... your stomach...
every organ... every cell... bathed in this healing light...
Your heart beating steadily... calmly... peacefully...

<snap/>

<pause duration="600ms"/>

And now... something interesting is happening...
As your body relaxes more and more...
your mind is becoming wonderfully clear...
<cmd>focused and receptive</cmd>... open to positive change...

<pause duration="2000ms"/>

I want you to imagine yourself standing at the top of a beautiful staircase...
Ten steps leading down... to the most peaceful place you have ever known...

With each step... you will go <cmd pitch="-1" rate="0.9">ten times deeper</cmd>...

<pause duration="800ms"/>

Step ten... taking the first step down... already feeling more relaxed...
Step nine... going deeper... your body so heavy and comfortable...

<pause duration="500ms"/>

Step eight... drifting down... further and further...
Step seven... <cmd>deeper and deeper</cmd>... so peaceful...

<pause duration="500ms"/>

Step six... halfway there... and already so deeply relaxed...
Step five... the warm light growing brighter around you...

<pause duration="500ms"/>

Step four... your conscious mind can rest now...
Step three... almost there... so deep... so calm...

<pause duration="500ms"/>

Step two... <cmd pitch="-2" rate="0.85">letting go of everything</cmd>...

<snap/>

<pause duration="1000ms"/>

Step one... and you are there now...
In the most peaceful... beautiful... safe place imaginable...

<pause duration="3000ms"/>

And in this place of deep relaxation...
your subconscious mind is completely open...
ready to accept positive suggestions...
ready for wonderful changes...

<pause duration="2000ms"/>

You are a person of great strength and capability...
Every day... in every way... you are growing stronger...
More confident... more resilient... more at peace...

<pause duration="1500ms"/>

The challenges that once seemed overwhelming...
now appear manageable... even small...
Because you have discovered something powerful within yourself...

<cmd pitch="-1.5" rate="0.9">You have the power to change</cmd>...

<pause duration="1000ms"/>

And this power grows stronger every day...
Like a muscle that becomes more powerful with each use...
Your inner strength... your confidence... your peace of mind...
All growing... expanding... <cmd>becoming more and more a part of who you are</cmd>...

<pause duration="2000ms"/>

Now imagine yourself in the future...
See yourself handling situations with calm confidence...
Notice how others respond to your peaceful energy...
<cmd pitch="-1" rate="0.9">Feel how good it feels to be this version of yourself</cmd>...

<pause duration="1500ms"/>

This is not a fantasy... this is your future reality...
Because the changes happening now... in this deep state...
are real... and lasting... and permanent...

<pause duration="2000ms"/>

<snap/>

Every cell in your body is absorbing these truths...
Every neural pathway is being rewired for success...
For confidence... for peace... for joy...

<pause duration="1000ms"/>

And you know... the beautiful thing about your subconscious mind...
is that it continues to work... even when you are not aware of it...
Processing... integrating... <cmd>making these changes automatic</cmd>...

<pause duration="1500ms"/>

So that tomorrow... and the next day... and every day after...
you will notice yourself responding differently...
More calmly... more confidently... more peacefully...

<pause duration="2000ms"/>

And now... it is time to begin your gentle return...
But know that everything we have discussed today...
remains firmly planted in your subconscious mind...

<pause duration="1000ms"/>

I am going to count from one to five...
and with each number... you will become more alert...
more awake... while keeping all the positive changes...

<pause duration="800ms"/>

One... beginning to return... feeling wonderful...
Two... becoming more aware of your surroundings...
Three... <cmd pitch="1" rate="1.1">energy returning to your body</cmd>... feeling refreshed...

<pause duration="500ms"/>

Four... almost fully awake now... feeling amazing...
And five... <cmd>eyes open</cmd>... fully alert... refreshed... and transformed...

<pause duration="1000ms"/>

Welcome back... take a moment to enjoy how good you feel...
"""

SHORT_AFFIRMATIONS = [
    "I am confident",
    "I am calm",
    "I succeed easily",
    "I am focused",
    "I choose peace",
    "My mind is clear",
    "I am powerful",
]

LARGE_AFFIRMATIONS = [
    "I am deeply confident in my abilities",
    "I am calm and centered",
    "I succeed easily and naturally",
    "I am focused and present",
    "I choose peace in every moment",
    "My mind is clear and sharp",
    "I am powerful beyond measure",
    "I radiate positive energy",
    "I am worthy of great things",
    "I embrace change with courage",
    "My body is strong and healthy",
    "I attract abundance effortlessly",
    "I am grateful for this moment",
    "I trust my inner wisdom",
    "I release all tension now",
    "I am becoming my best self",
    "I handle challenges with grace",
    "I am at peace with myself",
    "I create my own happiness",
    "I am enough exactly as I am",
]


# ─── Timer utility ───────────────────────────────────────────────────────────

@contextmanager
def timer(label: str, results: dict):
    """Context manager that records elapsed seconds into results[label]."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    results[label] = round(elapsed, 4)
    print(f"  {label}: {elapsed:.2f}s")


def _resample_if_needed(audio, orig_sr, target_sr):
    if orig_sr == target_sr:
        return audio
    import librosa
    return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)


def _to_stereo(audio):
    if audio.ndim == 1:
        return np.column_stack([audio, audio])
    return audio


def _pad_or_trim(audio, target_samples):
    current = audio.shape[0]
    if current == target_samples:
        return audio
    if current < target_samples:
        padding = np.zeros((target_samples - current, 2), dtype=audio.dtype)
        return np.concatenate([audio, padding], axis=0)
    return audio[:target_samples]


# ─── Benchmark runner ────────────────────────────────────────────────────────

def run_benchmark(scale: str = "short", seed: int = 42) -> dict:
    """Run full pipeline benchmark and return per-stage timings."""
    script_text = LARGE_SCRIPT if scale == "large" else SHORT_SCRIPT
    affirmations = LARGE_AFFIRMATIONS if scale == "large" else SHORT_AFFIRMATIONS
    voice = "af_heart"
    sr = OUTPUT_SAMPLE_RATE
    rng = np.random.default_rng(seed)

    results = {"scale": scale, "seed": seed, "output_sr": sr, "tts_sr": TTS_SAMPLE_RATE}
    total_start = time.perf_counter()

    # Stage 1: Parse script
    with timer("parse_script", results):
        segments = parse_script(script_text)
    results["segment_count"] = len(segments)
    tts_segments = [s for s in segments if s["type"] in ("text", "command", "drop_cue")]
    results["tts_segment_count"] = len(tts_segments)

    # Stage 2: Shepherd TTS + effects + resample
    with timer("render_shepherd", results):
        shepherd_audio = _render_shepherd_bench(segments, voice, sr)
    shepherd_duration_sec = shepherd_audio.shape[0] / sr
    results["shepherd_duration_sec"] = round(shepherd_duration_sec, 2)

    # Determine session length
    length_sec = max(int(shepherd_duration_sec), 60)
    results["session_length_sec"] = length_sec

    # Stage 3: Swarm TTS + resample + scheduling
    with timer("render_swarm", results):
        swarm_audio = _render_swarm_bench(affirmations, length_sec, sr, voice, rng)
    results["affirmation_count"] = len(affirmations)

    # Stage 4: Generate binaural bed
    with timer("generate_bed", results):
        bed_audio = generate_bed(duration_sec=length_sec, sr=sr, rng=rng)

    # Stage 5: Pad/trim all layers
    target_samples = length_sec * sr
    with timer("pad_trim", results):
        shepherd_audio = _pad_or_trim(shepherd_audio, target_samples)
        swarm_audio = _pad_or_trim(swarm_audio, target_samples)
        bed_audio = _pad_or_trim(bed_audio, target_samples)
    results["total_samples"] = target_samples

    # Stage 6: Mix layers (gain envelopes + boundary events + limiter)
    boundary_events = select_boundary_events(rng)
    with timer("mix_layers", results):
        mixed = mix_layers(
            shepherd=shepherd_audio,
            swarm=swarm_audio,
            bed=bed_audio,
            sr=sr,
            apply_epochs=True,
            boundary_events=boundary_events,
            rng=rng,
        )

    # Stage 7: Write WAV
    temp_path = os.path.join(tempfile.gettempdir(), f"hypnogen_bench_{scale}.wav")
    with timer("write_wav", results):
        write_wav(temp_path, mixed, sr)

    output_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
    results["output_size_mb"] = round(output_size_mb, 2)

    # Clean up
    os.unlink(temp_path)

    total_elapsed = time.perf_counter() - total_start
    results["total"] = round(total_elapsed, 4)

    # Compute stage percentages
    stage_keys = [
        "parse_script", "render_shepherd", "render_swarm",
        "generate_bed", "pad_trim", "mix_layers", "write_wav",
    ]
    for key in stage_keys:
        if key in results and total_elapsed > 0:
            results[f"{key}_pct"] = round(results[key] / total_elapsed * 100, 1)

    return results


def _render_shepherd_bench(segments, voice, target_sr):
    """Shepherd renderer matching web.py logic, without progress callbacks."""
    tts_sr = TTS_SAMPLE_RATE
    mono_parts = []
    for segment in segments:
        seg_type = segment["type"]

        if seg_type == "text":
            audio, _ = synthesize(segment["text"], voice=voice, speed=0.9)
            mono_parts.append(audio)

        elif seg_type == "command":
            audio, _ = synthesize(segment["text"], voice=voice, speed=0.9)
            pitch = segment.get("pitch", 0.0)
            rate = segment.get("rate", 1.0)
            if pitch != 0.0 or rate != 1.0:
                audio = apply_analog_marking(audio, tts_sr, pitch_shift=pitch, rate=rate)
            mono_parts.append(audio)

        elif seg_type == "pause":
            duration_ms = segment["duration_ms"]
            pause_samples = int((duration_ms / 1000) * tts_sr)
            mono_parts.append(np.zeros(pause_samples, dtype=np.float32))

        elif seg_type == "snap":
            from hypnogen.core.epochs import generate_boundary_event
            snap = generate_boundary_event("snap", sr=tts_sr)
            mono_parts.append(snap[:, 0].astype(np.float32))

        elif seg_type == "drop_cue":
            word = segment.get("word", "drop")
            word_audio, _ = synthesize(word, voice=voice, speed=0.7)
            word_audio = apply_analog_marking(word_audio, tts_sr, pitch_shift=-3.0, rate=0.8)
            mono_parts.append(word_audio.astype(np.float32))

    if not mono_parts:
        return np.zeros((1, 2), dtype=np.float32)
    mono_concat = np.concatenate(mono_parts)
    mono_resampled = _resample_if_needed(mono_concat, tts_sr, target_sr)
    return _to_stereo(mono_resampled)


def _render_swarm_bench(affirmations, duration_sec, sr, voice, rng):
    """Swarm renderer matching web.py logic, without progress callbacks."""
    tts_sr = TTS_SAMPLE_RATE
    affirmation_audios = []
    for aff in affirmations:
        audio, _ = synthesize(aff, voice=voice, speed=1.3)
        affirmation_audios.append(audio)
    swarm_at_tts_sr = generate_swarm(affirmation_audios, duration_sec, sr=tts_sr, rng=rng)
    left = _resample_if_needed(swarm_at_tts_sr[:, 0], tts_sr, sr)
    right = _resample_if_needed(swarm_at_tts_sr[:, 1], tts_sr, sr)
    return np.column_stack([left, right])


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Hypnogen pipeline benchmark")
    parser.add_argument(
        "--scale",
        choices=["short", "large"],
        default="short",
        help="Script scale: short (~60s) or large (~15-18min)",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--warmup", action="store_true",
        help="Run a tiny TTS warmup before benchmarking"
    )
    parser.add_argument(
        "--tag", type=str, default=None,
        help="Tag for this benchmark run (e.g., 'baseline', 'vectorized-epochs')"
    )
    args = parser.parse_args()

    # Warm up TTS model (first call downloads/loads model)
    if args.warmup:
        print("Warming up TTS model...")
        synthesize("warmup", voice="af_heart", speed=1.0)
        print("Warmup complete.\n")

    print(f"Running benchmark (scale={args.scale}, seed={args.seed})...\n")
    results = run_benchmark(scale=args.scale, seed=args.seed)

    # Add metadata
    results["timestamp"] = datetime.now(timezone.utc).isoformat()
    results["tag"] = args.tag or "untagged"

    # Print summary
    print(f"\n{'='*60}")
    print(f"TOTAL: {results['total']:.2f}s")
    print(f"Session length: {results['session_length_sec']}s")
    print(f"Output size: {results['output_size_mb']:.1f} MB")
    print(f"{'='*60}")
    print("\nStage breakdown:")
    for key in ["parse_script", "render_shepherd", "render_swarm",
                 "generate_bed", "pad_trim", "mix_layers", "write_wav"]:
        pct = results.get(f"{key}_pct", 0)
        val = results.get(key, 0)
        bar = "#" * int(pct / 2)
        print(f"  {key:20s} {val:8.2f}s  ({pct:5.1f}%)  {bar}")

    # Save results
    os.makedirs(BENCHMARKS_DIR, exist_ok=True)
    tag = args.tag or "untagged"
    filename = f"{tag}_{args.scale}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(BENCHMARKS_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {filepath}")

    return results


if __name__ == "__main__":
    main()
