"""TTS-only RTF benchmark harness.

This module provides a standalone benchmark for TTS providers,
measuring RTF (Real-Time Factor) throughput with cold and warm runs.
"""

import argparse
import io
import json
import time
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import statistics
import tempfile
import wave
import struct
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def get_git_sha() -> Optional[str]:
    """Get current git SHA."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_machine_info() -> Dict[str, Any]:
    """Get machine hardware information."""
    info = {
        "platform": "unknown",
        "hardware": "unknown",
        "cpu": "unknown",
        "memory_gb": 0
    }
    
    try:
        # Try macOS system_profiler
        result = subprocess.run(
            ['system_profiler', 'SPHardwareDataType', '-json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data and len(data) > 0:
                hw = data[0].get('_items', [{}])[0]
                info['platform'] = 'macOS'
                info['hardware'] = hw.get('machine_model', 'unknown')
                info['cpu'] = hw.get('chip_type') or hw.get('cpu_type', 'unknown')
                memory_mb = hw.get('physical_memory', '0')
                if isinstance(memory_mb, str):
                    memory_mb = memory_mb.replace(' GB', '').replace(' MB', '')
                    try:
                        info['memory_gb'] = float(memory_mb)
                    except ValueError:
                        pass
    except Exception as e:
        info['error'] = str(e)
    
    return info


def validate_audio(audio_data: bytes, expected_duration: float) -> Dict[str, Any]:
    """Perform basic audio sanity checks.
    
    Returns dict with:
        - passed: bool
        - checks: dict of individual check results
        - error: str (if failed)
    """
    checks = {
        "non_empty": False,
        "valid_wav": False,
        "no_nan_inf": False,
        "duration_in_bounds": False,
        "no_clipping": False
    }
    
    try:
        # Check non-empty
        if len(audio_data) > 0:
            checks["non_empty"] = True
        else:
            return {"passed": False, "checks": checks, "error": "Audio data is empty"}
        
        # Write to temp file and read as WAV
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(audio_data)
            temp_path = f.name
        
        try:
            with wave.open(temp_path, 'rb') as wav:
                checks["valid_wav"] = True
                n_channels = wav.getnchannels()
                sample_width = wav.getsampwidth()
                framerate = wav.getframerate()
                n_frames = wav.getnframes()
                
                # Read all frames
                frames = wav.readframes(n_frames)
                
                # Convert to samples based on sample width
                if sample_width == 2:
                    fmt = f'{len(frames) // 2}h'
                    samples = struct.unpack(fmt, frames)
                else:
                    return {"passed": False, "checks": checks, "error": f"Unsupported sample width: {sample_width}"}
                
                # Check for NaN/Inf (not applicable to integer samples, but check for extreme values)
                max_val = max(abs(s) for s in samples)
                checks["no_nan_inf"] = True  # Integer samples can't be NaN
                
                # Check duration bounds (±20%)
                actual_duration = n_frames / framerate
                duration_diff = abs(actual_duration - expected_duration) / expected_duration
                checks["duration_in_bounds"] = duration_diff <= 0.20
                
                # Check for hard clipping (> 99% of max int16)
                max_int16 = 32767
                clipping_threshold = int(max_int16 * 0.99)
                clipped_samples = sum(1 for s in samples if abs(s) > clipping_threshold)
                checks["no_clipping"] = clipped_samples < len(samples) * 0.01
        finally:
            os.unlink(temp_path)
        
        passed = all(checks.values())
        return {
            "passed": passed,
            "checks": checks,
            "duration_sec": actual_duration if 'actual_duration' in dir() else 0,
            "error": None if passed else f"Failed checks: {[k for k, v in checks.items() if not v]}"
        }
        
    except Exception as e:
        return {"passed": False, "checks": checks, "error": str(e)}


@dataclass
class BenchmarkResult:
    """Single benchmark run result."""
    wall_time_sec: float
    audio_duration_sec: float
    rtf: float
    sanity_checks_passed: bool
    sanity_details: Dict[str, Any]


@dataclass
class CaseResult:
    """Results for a single corpus case."""
    case_id: str
    cold: Dict[str, Any]
    warm: Dict[str, Any]


def _encode_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    """Encode mono float audio in [-1, 1] as 16-bit PCM WAV bytes."""
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    clipped = np.clip(audio, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())
    return buffer.getvalue()


def normalize_audio_result(result: Any) -> bytes:
    """Normalize various audio return formats to raw bytes.
    
    Handles:
    - bytes
    - (bytes, sample_rate)
    - list of bytes
    - list of (bytes, sample_rate)
    """
    if isinstance(result, bytes):
        return result
    
    if isinstance(result, np.ndarray):
        return _encode_wav_bytes(result, 24000)
    
    if isinstance(result, tuple):
        # Common provider output: (audio_array, sample_rate)
        audio = result[0]
        sample_rate = int(result[1]) if len(result) > 1 else 24000
        if isinstance(audio, bytes):
            return audio
        if isinstance(audio, np.ndarray):
            return _encode_wav_bytes(audio, sample_rate)
        return audio
    
    if isinstance(result, list):
        if not result:
            return b""

        if all(
            isinstance(chunk, tuple)
            and len(chunk) >= 2
            and isinstance(chunk[0], np.ndarray)
        for chunk in result):
            sample_rate = int(result[0][1])
            merged_audio = np.concatenate(
                [np.asarray(chunk[0], dtype=np.float32).reshape(-1) for chunk in result]
            )
            return _encode_wav_bytes(merged_audio, sample_rate)

        if len(result) == 1:
            return normalize_audio_result(result[0])

        normalized_chunks = []
        for chunk in result:
            normalized = normalize_audio_result(chunk)
            if isinstance(normalized, bytes):
                normalized_chunks.append(normalized)
        return b"".join(normalized_chunks)
    
    return result


def synthesize_with_timing(
    provider,
    text: str,
    voice: str,
    speed: float = 1.0
) -> tuple[bytes, float]:
    """Synthesize audio and return (audio_data, wall_time)."""
    start = time.perf_counter()
    
    # Use the provider's synthesize method
    # Assuming provider has synthesize_batch or similar
    if hasattr(provider, "synthesize_batch"):
        result = provider.synthesize_batch([text], voice=voice, speed=speed)
    else:
        result = provider.synthesize(text, voice=voice, speed=speed)
    
    audio_data = normalize_audio_result(result)

    
    elapsed = time.perf_counter() - start
    return audio_data, elapsed


def run_benchmark(
    corpus_path: Path,
    provider_name: str,
    voice: str,
    compute_units: Optional[str] = None,
    warm_repeats: int = 5,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Run full benchmark and return results dict."""
    
    # Load corpus
    with open(corpus_path) as f:
        corpus = json.load(f)
    
    # Import TTS provider
    from hypnogen.core.tts_providers import get_provider
    
    provider_kwargs = {}
    if compute_units and provider_name == 'coreml':
        provider_kwargs['compute_units'] = compute_units
    
    # Initialize provider
    provider = get_provider(provider_name, **provider_kwargs)
    
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "git_sha": get_git_sha(),
        "machine_info": get_machine_info(),
        "config": {
            "provider": provider_name,
            "compute_units": compute_units,
            "voice": voice,
            "warm_repeats": warm_repeats,
            "corpus_version": corpus.get("version", "unknown")
        },
        "runs": []
    }
    
    # Start log capture for CoreML
    log_process = None
    log_file_handle = None
    if provider_name == 'coreml':
        evidence_dir = Path('.sisyphus/evidence')
        evidence_dir.mkdir(parents=True, exist_ok=True)
        log_file = evidence_dir / 'coreml-log-stream.txt'
        log_file_handle = open(log_file, 'w')
        log_process = subprocess.Popen(
            ['log', 'stream', '--predicate', 
             'sender == "AppleNeuralEngine" OR subsystem == "com.apple.CoreML"',
             '--info'],
            stdout=log_file_handle,
            stderr=subprocess.STDOUT
        )
        # Give log stream a moment to start
        time.sleep(0.5)
    
    try:
        for case in corpus['cases']:
            print(f"Benchmarking case: {case['case_id']}")
            
            # Combine script and affirmations for synthesis
            full_text = case['script_text'] + ' ' + ' '.join(case['affirmations'][:3])
            
            # Cold run
            print("  Cold run...")
            audio_data, cold_time = synthesize_with_timing(provider, full_text, voice)
            
            # Estimate expected duration (rough estimate: 150 words/minute)
            word_count = len(full_text.split())
            expected_duration = (word_count / 150) * 60
            
            # Validate audio
            sanity_result = validate_audio(audio_data, expected_duration)
            
            cold_result = {
                "wall_time_sec": cold_time,
                "audio_duration_sec": sanity_result.get("duration_sec", expected_duration),
                "rtf": sanity_result.get("duration_sec", expected_duration) / cold_time if cold_time > 0 else 0,
                "sanity_checks_passed": sanity_result["passed"],
                "sanity_details": sanity_result
            }
            
            # Warm runs
            print(f"  Warm runs ({warm_repeats} repeats)...")
            warm_times = []
            for i in range(warm_repeats):
                _, t = synthesize_with_timing(provider, full_text, voice)
                warm_times.append(t)
            
            mean_time = statistics.mean(warm_times)
            std_time = statistics.stdev(warm_times) if len(warm_times) > 1 else 0
            
            warm_result = {
                "mean_wall_time_sec": mean_time,
                "std_wall_time_sec": std_time,
                "mean_rtf": cold_result["audio_duration_sec"] / mean_time if mean_time > 0 else 0,
                "repeats": warm_repeats,
                "all_times": warm_times
            }
            
            case_result = {
                "case_id": case['case_id'],
                "cold": cold_result,
                "warm": warm_result
            }
            results['runs'].append(case_result)
            
            print(f"  Cold RTF: {cold_result['rtf']:.3f}, Warm RTF: {warm_result['mean_rtf']:.3f}")
    
    finally:
        if log_process:
            log_process.terminate()
            try:
                log_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                log_process.kill()
        if log_file_handle:
            log_file_handle.close()
    
    provider.shutdown() if hasattr(provider, 'shutdown') else None
    
    # Save results
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {output_path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='TTS-only RTF benchmark harness'
    )
    parser.add_argument(
        '--provider',
        choices=['pytorch', 'coreml', 'quantized'],
        required=True,
        help='TTS provider to benchmark'
    )
    parser.add_argument(
        '--compute-units',
        choices=['ALL', 'CPU_AND_GPU', 'CPU_ONLY'],
        default=None,
        help='CoreML compute units (only for coreml provider)'
    )
    parser.add_argument(
        '--voice',
        default='af_heart',
        help='Voice to use for synthesis'
    )
    parser.add_argument(
        '--corpus',
        type=Path,
        default=Path('hypnogen/benchmarks/corpus/tts_corpus.json'),
        help='Path to corpus JSON file'
    )
    parser.add_argument(
        '--out',
        type=Path,
        default=None,
        help='Output JSON file path'
    )
    parser.add_argument(
        '--warm-repeats',
        type=int,
        default=5,
        help='Number of warm-up repeats'
    )
    
    args = parser.parse_args()
    
    if not args.corpus.exists():
        print(f"Error: Corpus file not found: {args.corpus}")
        sys.exit(1)
    
    if args.out is None:
        # Default output path
        benches_dir = Path('.sisyphus/benchmarks')
        benches_dir.mkdir(parents=True, exist_ok=True)
        cu_suffix = f"_{args.compute_units.lower()}" if args.compute_units else ""
        args.out = benches_dir / f"tts_only_{args.provider}{cu_suffix}_{args.voice}.json"
    
    results = run_benchmark(
        corpus_path=args.corpus,
        provider_name=args.provider,
        voice=args.voice,
        compute_units=args.compute_units,
        warm_repeats=args.warm_repeats,
        output_path=args.out
    )
    
    # Print summary
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    for run in results['runs']:
        print(f"\nCase: {run['case_id']}")
        print(f"  Cold RTF: {run['cold']['rtf']:.3f} ({run['cold']['wall_time_sec']:.2f}s)")
        print(f"  Warm RTF: {run['warm']['mean_rtf']:.3f} ± {run['warm']['std_wall_time_sec']:.3f}s")
        print(f"  Sanity checks: {'PASS' if run['cold']['sanity_checks_passed'] else 'FAIL'}")


if __name__ == '__main__':
    main()
