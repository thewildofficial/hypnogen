# TTS Provider Benchmark Matrix Report

**Date**: 2026-02-18
**Git SHA**: `fc54b7e`
**Corpus Version**: 1.0
**Voice**: `af_heart`
**Warm Repeats**: 5 per case

---

## Hardware

| Field | Value |
|-------|-------|
| Platform | macOS (Apple Silicon) |
| CPU | Apple M2 Air |
| Memory | 8 GB unified |
| Note | `machine_info` fields reported as "unknown" due to detection bug; hardware confirmed as M2 Air from task context |

---

## Benchmark Corpus

| Case ID | Expected Audio Duration |
|---------|------------------------|
| `short_relaxation` | ~36s (PyTorch/Quantized) / ~8s (CoreML†) |
| `medium_confidence` | ~60s (PyTorch/Quantized) / ~11s (CoreML†) |
| `long_sleep` | ~82s (PyTorch/Quantized) / ~13s (CoreML†) |

> † CoreML providers produced truncated audio (failed `duration_in_bounds` sanity check), so their RTF numbers are computed against shorter outputs. This inflates their apparent speed — the audio is fast but **wrong**.

---

## Per-Case Results

### Case: `short_relaxation`

| Provider | Cold RTF | Warm RTF (mean) | Warm StdDev (s) | Audio Duration (s) | Sanity |
|----------|----------|-----------------|-----------------|---------------------|--------|
| PyTorch | 3.30 | 4.79 | 2.12 | 36.43 | ✅ PASS |
| CoreML CPU_AND_GPU | 2.18 | 22.84 | 0.004 | 8.40 | ❌ FAIL |
| CoreML ALL | 1.21 | 2.36 | 0.54 | 8.43 | ❌ FAIL |
| Quantized | 2.78 | 4.70 | 0.64 | 36.43 | ✅ PASS |

### Case: `medium_confidence`

| Provider | Cold RTF | Warm RTF (mean) | Warm StdDev (s) | Audio Duration (s) | Sanity |
|----------|----------|-----------------|-----------------|---------------------|--------|
| PyTorch | 4.48 | 5.74 | 0.80 | 59.68 | ✅ PASS |
| CoreML CPU_AND_GPU | 16.49 | 19.60 | 0.006 | 10.74 | ❌ FAIL |
| CoreML ALL | 1.98 | 2.10 | 0.32 | 10.75 | ❌ FAIL |
| Quantized | 3.85 | 3.83 | 5.55 | 59.68 | ✅ PASS |

### Case: `long_sleep`

| Provider | Cold RTF | Warm RTF (mean) | Warm StdDev (s) | Audio Duration (s) | Sanity |
|----------|----------|-----------------|-----------------|---------------------|--------|
| PyTorch | 4.13 | 4.30 | 2.75 | 82.43 | ✅ PASS |
| CoreML CPU_AND_GPU | 22.25 | 22.27 | 0.024 | 13.08 | ❌ FAIL |
| CoreML ALL | 2.86 | 2.82 | 0.09 | 13.09 | ❌ FAIL |
| Quantized | 4.48 | 2.73 | 3.27 | 82.43 | ✅ PASS |

---

## Aggregate Summary (Mean Across All 3 Cases)

| Provider | Avg Cold RTF | Avg Warm RTF | Avg Warm StdDev (s) | Sanity Pass Rate |
|----------|-------------|-------------|---------------------|------------------|
| **PyTorch** | 3.97 | 4.94 | 1.89 | **3/3 (100%)** |
| CoreML CPU_AND_GPU | 13.64 | 21.57 | 0.011 | 0/3 (0%) |
| CoreML ALL | 2.02 | 2.43 | 0.32 | 0/3 (0%) |
| **Quantized** | 3.70 | 3.75 | 3.15 | **3/3 (100%)** |

---

## Winner Per Metric

| Metric | Winner | Value | Runner-up | Value | Improvement |
|--------|--------|-------|-----------|-------|-------------|
| **Best Cold RTF** | CoreML ALL | 2.02 | Quantized | 3.70 | 45% faster |
| **Best Warm RTF** | CoreML ALL | 2.43 | Quantized | 3.75 | 35% faster |
| **Lowest StdDev** | CoreML CPU_AND_GPU | 0.011s | CoreML ALL | 0.32s | 97% lower variance |
| **Best Sanity Pass Rate** | PyTorch / Quantized (tie) | 100% | CoreML ALL / CPU_AND_GPU | 0% | ∞ |
| **Best Warm RTF (sanity-passing only)** | **Quantized** | **3.75** | PyTorch | 4.94 | **24% faster** |

> **Key finding**: CoreML ALL has the best raw RTF but produces **truncated, incorrect audio** (0% sanity pass rate). Among providers that produce correct audio, **Quantized** is the fastest.

---

## Reproduction Commands

All benchmarks were run from the project root at commit `fc54b7e`.

```bash
# PyTorch (default provider)
uv run python -m hypnogen.benchmark_tts --provider pytorch --warm-repeats 5 --out .sisyphus/benchmarks/tts_pytorch_m2air.json

# CoreML CPU_AND_GPU
uv run python -m hypnogen.benchmark_tts --provider coreml --compute-units CPU_AND_GPU --warm-repeats 5 --out .sisyphus/benchmarks/tts_coreml_cpugpu_m2air.json

# CoreML ALL
uv run python -m hypnogen.benchmark_tts --provider coreml --compute-units ALL --warm-repeats 5 --out .sisyphus/benchmarks/tts_coreml_all_m2air.json

# Quantized (ONNX int8)
uv run python -m hypnogen.benchmark_tts --provider quantized --warm-repeats 5 --out .sisyphus/benchmarks/tts_quantized_m2air.json
```

---

## Notes

1. **RTF (Real-Time Factor)** = `audio_duration / wall_time`. Higher is faster (RTF 2.0 means audio is generated 2× faster than playback).
2. CoreML providers failed `duration_in_bounds` on all cases — they produced ~8–13s audio regardless of input length. This is a fundamental correctness issue, not just a performance concern.
3. The `machine_info` block reported "unknown" for all fields due to a detection bug in the benchmark harness. The actual hardware is confirmed as Apple M2 Air (8GB) from the benchmark execution context.
4. Quantized provider showed high variance on `medium_confidence` (one run at 25.5s vs others at ~13s), suggesting occasional outlier behavior.
