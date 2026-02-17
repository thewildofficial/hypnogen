# TTS Runtime Provider Decision

**Date**: 2026-02-18
**Git SHA**: `fc54b7e`
**Benchmark Report**: [`benchmark-matrix-report.md`](benchmark-matrix-report.md)

---

## Decision

**Recommended default provider: `pytorch`**

---

## Rationale

### Why not CoreML ALL (fastest raw RTF)?

CoreML ALL achieved the best raw warm RTF of **2.43** (vs PyTorch's 4.94), but it **fails sanity checks on 100% of test cases**. Every CoreML run (both ALL and CPU_AND_GPU configurations) produced truncated audio that fails the `duration_in_bounds` check — outputting ~8–13 seconds regardless of input length. This is a **correctness failure**, not a marginal quality issue. CoreML cannot be recommended as a default until this is resolved.

### Why not Quantized (fastest correct provider)?

Quantized (ONNX int8) produced correct audio (100% sanity pass rate) with the best warm RTF among correct providers at **3.75** — 24% faster than PyTorch's 4.94. However:

- **High variance**: Warm StdDev of 3.15s (vs PyTorch's 1.89s), with one `medium_confidence` run spiking to 25.5s (2× the mean).
- **Inconsistent scaling**: RTF ranges from 2.73 (long_sleep) to 4.70 (short_relaxation), suggesting unpredictable behavior across input sizes.

Quantized is a viable alternative but PyTorch is more predictable for a default.

### Why PyTorch?

- **100% sanity pass rate** — all audio outputs are correct in duration and content.
- **Predictable performance**: Warm RTF of 4.94 with moderate variance (StdDev 1.89s).
- **No additional dependencies**: Works out of the box without CoreML model conversion or ONNX quantization.
- **Proven reliability**: The existing codebase and tests were built around PyTorch.

---

## RTF Threshold Check

**Target**: ≤ 2.0 RTF (audio generated at least 2× faster than real-time)

| Provider | Warm RTF | Meets ≤2.0? | Notes |
|----------|----------|-------------|-------|
| PyTorch | 4.94 | ❌ **NO** | 2.5× slower than target |
| CoreML CPU_AND_GPU | 21.57 | ❌ NO | Fails sanity; RTF misleading |
| CoreML ALL | 2.43 | ❌ NO | Closest, but fails sanity |
| Quantized | 3.75 | ❌ **NO** | 1.9× slower than target |

> **⚠️ No provider currently meets the ≤2.0 RTF target while producing correct audio.**
>
> CoreML ALL achieves 2.43 RTF but on truncated (incorrect) audio. If the CoreML correctness bug is fixed, it is the most likely candidate to meet the threshold. Otherwise, alternative approaches (streaming, chunking, or native Swift Kokoro) will be required.

---

## Fallback Chain

```
pytorch → quantized → error("No TTS provider available")
```

1. **`pytorch`** (default): Reliable, correct output, acceptable latency for batch generation.
2. **`quantized`** (fallback): Faster on large inputs (RTF 2.73 on `long_sleep`), correct output, but higher variance.
3. **Error**: CoreML providers are excluded from the fallback chain due to 0% sanity pass rate. Do not fall back to a provider that produces incorrect audio.

### Why CoreML is excluded from the fallback chain

Both CoreML configurations (CPU_AND_GPU and ALL) fail `duration_in_bounds` on every test case. Including them in a fallback chain would silently produce broken audio — the worst possible user experience for a hypnosis session generator.

---

## Conditions for Changing This Decision

This decision should be re-evaluated when **any** of the following occur:

1. **CoreML correctness fix**: If the `duration_in_bounds` failure is resolved and CoreML ALL passes sanity checks, re-benchmark. If it achieves ≤2.0 RTF with correct audio, it becomes the recommended default.

2. **Quantized stability improvement**: If quantized provider variance is reduced (StdDev < 1.0s consistently), it could replace PyTorch as the default due to its faster RTF.

3. **New provider available**: If a Swift-native Kokoro implementation or other provider becomes available, benchmark it against this matrix.

4. **RTF target change**: If the ≤2.0 RTF requirement is relaxed (e.g., for batch-only use cases where real-time is not needed), the decision calculus changes.

5. **Hardware change**: These benchmarks are specific to M2 Air (8GB). Results on M-series Pro/Max/Ultra chips or machines with more memory may differ significantly.

6. **Kokoro model update**: A new version of the Kokoro model or its CoreML conversion tooling may resolve the truncation bug.
