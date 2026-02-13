#!/usr/bin/env python3
"""
Quick benchmark to verify CoreML full synthesizer speedup.
Compares:
1. Hybrid: Duration (CoreML) → F0Ntrain (PyTorch) → Decoder (CoreML)
2. Full CoreML: Duration (CoreML) → Alignment (Python) → Synthesizer (CoreML)
"""

import time
import numpy as np
import coremltools as ct
from pathlib import Path
import sys

# Add vendor to path
sys.path.insert(0, str(Path(__file__).parent.parent / "vendor" / "kokoro-coreml"))

# Import Kokoro for text processing
from kokoro import KModel, KPipeline

# Paths
COREML_DIR = Path("coreml_models")
DURATION_MODEL = COREML_DIR / "kokoro_duration.mlpackage"
SYNTH_3S = COREML_DIR / "kokoro_synthesizer_3s.mlpackage"

def build_alignment_matrix(pred_dur_tokens: np.ndarray, trace_length: int, frame_count: int) -> np.ndarray:
    """Construct pred_aln_trg of shape (trace_length, frame_count) with one-hot repeats."""
    pred_dur = np.zeros((trace_length,), dtype=np.int64)
    L = min(trace_length, pred_dur_tokens.shape[-1])
    pred_dur[:L] = pred_dur_tokens[:L]
    
    repeat_idx = np.repeat(np.arange(trace_length), pred_dur)
    if repeat_idx.size > frame_count:
        repeat_idx = repeat_idx[:frame_count]
    else:
        pad = frame_count - repeat_idx.size
        last_idx = repeat_idx[-1] if repeat_idx.size > 0 else 0
        repeat_idx = np.concatenate([repeat_idx, np.full((pad,), last_idx, dtype=repeat_idx.dtype)])
    
    mat = np.zeros((trace_length, frame_count), dtype=np.float32)
    mat[repeat_idx, np.arange(frame_count)] = 1.0
    return mat


def benchmark_full_coreml(text="hello", voice="af_heart"):
    """Benchmark the full CoreML approach (no PyTorch F0Ntrain)."""
    print(f"\n{'='*60}")
    print("FULL COREML APPROACH")
    print(f"{'='*60}")
    
    # Load models
    print("Loading models...")
    t0 = time.time()
    duration_model = ct.models.MLModel(str(DURATION_MODEL))
    synth_model = ct.models.MLModel(str(SYNTH_3S))
    load_time = time.time() - t0
    print(f"  Models loaded in {load_time:.3f}s")
    
    # Get model specs
    synth_spec = synth_model.get_spec()
    input_shapes = {i.name: list(i.type.multiArrayType.shape) for i in synth_spec.description.input}
    trace_length = int(input_shapes['d'][-1])
    frame_count = int(input_shapes['pred_aln_trg'][-1])
    print(f"  Synthesizer: trace_length={trace_length}, frame_count={frame_count}")
    
    # Load Kokoro for text processing only (no inference)
    print("\nLoading Kokoro pipeline for text processing...")
    t0 = time.time()
    pipeline = KPipeline(lang_code='a', model=False)
    voice_pack = pipeline.load_voice(voice)
    
    # Get phonemes
    phonemes = None
    for _, ps, _ in pipeline(text, voice):
        phonemes = ps
        break
    print(f"  Phonemes: {phonemes}")
    print(f"  Pipeline loaded in {time.time() - t0:.3f}s")
    
    # Get vocab and convert phonemes to IDs
    vocab = KModel().vocab
    input_ids = [0] + [vocab.get(p, 0) for p in phonemes] + [0]
    ref_s = voice_pack[len(phonemes)-1]
    
    # Prepare duration inputs
    max_duration_len = 128  # From duration model spec
    input_ids_padded = input_ids + [0] * (max_duration_len - len(input_ids))
    input_ids_arr = np.array([input_ids_padded], dtype=np.int32)
    attention_mask = np.array([[1 if i < len(input_ids) else 0 for i in range(max_duration_len)]], dtype=np.int32)
    ref_s_arr = ref_s.numpy().reshape(1, 256).astype(np.float32)
    speed_arr = np.array([1.0], dtype=np.float32)
    
    # Warm up duration model
    print("\nWarming up duration model...")
    for _ in range(3):
        _ = duration_model.predict({
            'input_ids': input_ids_arr,
            'attention_mask': attention_mask,
            'ref_s': ref_s_arr,
            'speed': speed_arr
        })
    
    # Time duration inference
    print("\nTiming duration model...")
    times = []
    for _ in range(10):
        t0 = time.time()
        dur_out = duration_model.predict({
            'input_ids': input_ids_arr,
            'attention_mask': attention_mask,
            'ref_s': ref_s_arr,
            'speed': speed_arr
        })
        times.append(time.time() - t0)
    dur_time = np.mean(times)
    print(f"  Duration inference: {dur_time*1000:.2f}ms (avg of 10)")
    
    # Extract outputs
    d = dur_out['d']  # [1, 128, 640] - need to check shape
    t_en = dur_out['t_en']  # [1, 512, 128]
    pred_dur = dur_out['pred_dur']  # [1, 128]
    s = dur_out['s']  # [1, 128]
    
    print(f"  d shape: {d.shape}, t_en shape: {t_en.shape}")
    
    # Transpose d if needed (CoreML outputs channels-last sometimes)
    if d.shape[1] == 640:  # [1, 640, 128] - already correct
        pass
    elif d.shape[2] == 640:  # [1, 128, 640] - need transpose
        d = np.transpose(d, (0, 2, 1))
    
    # Build alignment matrix
    t0 = time.time()
    alignment = build_alignment_matrix(pred_dur.reshape(-1), trace_length, frame_count)
    align_time = time.time() - t0
    print(f"  Alignment matrix built in {align_time*1000:.2f}ms")
    
    # Pad/truncate to match synthesizer expected shapes
    def pad_time(x, T):
        h = x.shape[1]
        out = np.zeros((1, h, T), dtype=np.float32)
        t = min(T, x.shape[-1])
        out[:, :, :t] = x[:, :, :t]
        return out
    
    d_padded = pad_time(d, trace_length)
    t_en_padded = pad_time(t_en, trace_length)
    
    # Warm up synthesizer
    print("\nWarming up synthesizer...")
    synth_inputs = {
        'd': d_padded,
        't_en': t_en_padded,
        's': s.astype(np.float32),
        'ref_s': ref_s_arr,
        'pred_aln_trg': alignment
    }
    for _ in range(3):
        _ = synth_model.predict(synth_inputs)
    
    # Time synthesizer inference
    print("\nTiming synthesizer...")
    times = []
    for _ in range(10):
        t0 = time.time()
        synth_out = synth_model.predict(synth_inputs)
        times.append(time.time() - t0)
    synth_time = np.mean(times)
    print(f"  Synthesizer inference: {synth_time*1000:.2f}ms (avg of 10)")
    
    # Get audio output
    audio = synth_out['waveform'].squeeze()
    print(f"  Audio shape: {audio.shape}, duration: {len(audio)/24000:.2f}s")
    
    # Calculate RTF
    total_time = dur_time + align_time + synth_time
    audio_duration = len(audio) / 24000
    rtf = total_time / audio_duration
    
    print(f"\n{'='*60}")
    print("RESULTS - FULL COREML")
    print(f"{'='*60}")
    print(f"Duration model:   {dur_time*1000:.2f}ms")
    print(f"Alignment build:  {align_time*1000:.2f}ms")
    print(f"Synthesizer:      {synth_time*1000:.2f}ms")
    print(f"Total time:       {total_time*1000:.2f}ms")
    print(f"Audio duration:   {audio_duration:.2f}s")
    print(f"RTF:              {rtf:.3f} ({1/rtf:.1f}x real-time)")
    
    return {
        'total_time': total_time,
        'rtf': rtf,
        'audio': audio
    }


if __name__ == "__main__":
    # Check if models exist
    if not DURATION_MODEL.exists():
        print(f"ERROR: Duration model not found: {DURATION_MODEL}")
        print("Run from repo root directory")
        sys.exit(1)
    
    if not SYNTH_3S.exists():
        print(f"ERROR: Synthesizer model not found: {SYNTH_3S}")
        print("Copy from vendor/kokoro-coreml/coreml/")
        sys.exit(1)
    
    # Run benchmark
    result = benchmark_full_coreml("hello world")
    
    print(f"\n{'='*60}")
    print("VERIFICATION")
    print(f"{'='*60}")
    if result['rtf'] < 1.0:
        speedup = 1 / result['rtf']
        print(f"✅ SUCCESS: {speedup:.1f}x real-time speedup achieved!")
        print(f"   Target was 17x, got {speedup:.1f}x")
    else:
        print(f"⚠️  RTF > 1.0: {result['rtf']:.3f} (slower than real-time)")
    
    # Save audio for verification
    import wave
    with wave.open('/tmp/test_full_coreml.wav', 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(24000)
        audio_int16 = (result['audio'] * 32767).astype(np.int16)
        f.writeframes(audio_int16.tobytes())
    print(f"\nAudio saved to /tmp/test_full_coreml.wav for verification")
