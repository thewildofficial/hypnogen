# Hypnogen Benchmarking Guide

This document explains how to benchmark the TTS (Text-to-Speech) implementations in Hypnogen, specifically comparing **CoreML** (Apple Neural Engine) vs **PyTorch** runtimes.

## Table of Contents

- [Quick Start](#quick-start)
- [Understanding RTF](#understanding-rtf)
- [Prerequisites](#prerequisites)
- [Running TTS Benchmarks](#running-tts-benchmarks)
  - [Benchmarking PyTorch](#benchmarking-pytorch)
  - [Benchmarking CoreML](#benchmarking-coreml)
- [Comparing Results](#comparing-results)
- [Pipeline Benchmarks](#pipeline-benchmarks)
- [Full CoreML Benchmark](#full-coreml-benchmark)
- [Interpreting Results](#interpreting-results)

---

## End-to-End Installation

This section walks through setting up everything needed for CoreML vs PyTorch benchmarking from scratch.

### Step 1: Clone the Repository

```bash
git clone https://github.com/thewildofficial/hypnogen.git
cd hypnogen
```

### Step 2: Install Python Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### Step 3: Set up CoreML Models (Required for CoreML Benchmark)

The CoreML models must be converted from PyTorch. This is a one-time setup.

```bash
# Navigate to the Kokoro vendor package
cd vendor/kokoro-coreml

# Check what's needed - look at the README or scripts
ls -la

# The export script should be available
# Run the conversion (this may take 30+ minutes on first run)
python -m kokoro export --output_dir ../../coreml_models
```

If the above doesn't work, check for alternative export scripts:
```bash
# Alternative: check for export scripts
ls *.py
python export_synthesizers.py --help
```

### Step 4: Verify CoreML Models

After export, verify the models exist:
```bash
ls -la ../coreml_models/
```

You should see:
- `kokoro_duration.mlpackage`
- `kokoro_synthesizer_3s.mlpackage`
- `kokoro_decoder_only_3s.mlpackage` (or similar)
- `kokoro_f0n_3s.mlpackage`

### Step 5: Test the Setup

```bash
# Go back to repo root
cd ../..

# Test PyTorch TTS (should work out of the box)
python -c "from hypnogen.core.tts_providers.pytorch import PyTorchTTSProvider; p = PyTorchTTSProvider(); print('PyTorch OK')"

# Test CoreML TTS (requires models)
python -c "from hypnogen.core.tts_providers.coreml import CoreMLTTSProvider; c = CoreMLTTSProvider(); print('CoreML OK')"
```

### Step 6: Run the Benchmarks

Now you're ready to benchmark:

```bash
# Run PyTorch benchmark
python -m hypnogen.benchmarks.bench_tts_only \
  --provider pytorch \
  --out .sisyphus/benchmarks/tts_pytorch.json

# Run CoreML benchmark  
python -m hypnogen.benchmarks.bench_tts_only \
  --provider coreml \
  --compute-units ALL \
  --out .sisyphus/benchmarks/tts_coreml.json

# Compare results
python hypnogen/benchmarks/compare_tts_results.py \
  .sisyphus/benchmarks/tts_pytorch.json \
  .sisyphus/benchmarks/tts_coreml.json
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -e .

# 2. Run PyTorch benchmark
python -m hypnogen.benchmarks.bench_tts_only --provider pytorch --out .sisyphus/benchmarks/tts_pytorch.json

# 3. Run CoreML benchmark (on Mac with Apple Silicon)
python -m hypnogen.benchmarks.bench_tts_only --provider coreml --compute-units ALL --out .sisyphus/benchmarks/tts_coreml.json

# 4. Compare results
python hypnogen/benchmarks/compare_tts_results.py .sisyphus/benchmarks/tts_pytorch.json .sisyphus/benchmarks/tts_coreml.json
```

---

## Understanding RTF

**RTF (Real-Time Factor)** measures how fast the TTS engine runs compared to real-time audio playback:

| RTF Value | Meaning | Example |
|-----------|---------|---------|
| `RTF < 1.0` | Faster than real-time | 0.5 = 2x faster (produces 1s audio in 0.5s) |
| `RTF = 1.0` | Same as real-time | 1.0 = 1x (produces 1s audio in 1s) |
| `RTF > 1.0` | Slower than real-time | 2.0 = 0.5x (produces 1s audio in 2s) |

**Higher RTF = Better performance** (more audio per second of processing time)

---

## Prerequisites

### General
- Python 3.9+
- `pip install -e .` to install Hypnogen

### For PyTorch Benchmark
- PyTorch installed (included in Hypnogen dependencies)

### For CoreML Benchmark (Apple Silicon)
- Mac with Apple Silicon (M1/M2/M3/M4)
- `coremltools` installed
- **CoreML models must be set up** (see below)

#### Setting up CoreML Models

The CoreML models are NOT included in the repo (too large for git). You have two options:

**Option 1: Copy pre-converted models (if available)**
```bash
# If you have converted models somewhere
cp -r /path/to/models coreml_models/
```

**Option 2: Convert from PyTorch**
```bash
cd vendor/kokoro-coreml

# Download the base model if needed
# (check vendor/kokoro-coreml for instructions)

# Export CoreML models
python -m kokoro export --output_dir ../../coreml_models
```

The required models are:
- `kokoro_duration.mlpackage` - Duration prediction
- `kokoro_synthesizer_3s.mlpackage` - 3-second synthesis bucket
- `kokoro_decoder_only_3s.mlpackage` - Decoder (3s bucket)
- `kokoro_f0n_3s.mlpackage` - F0Ntrain model

### For log streaming (optional)
- `log` command available (macOS)

---

## Running TTS Benchmarks

### Benchmarking PyTorch

```bash
python -m hypnogen.benchmarks.bench_tts_only \
  --provider pytorch \
  --voice af_heart \
  --warm-repeats 5 \
  --out .sisyphus/benchmarks/tts_pytorch.json
```

Options:
- `--voice`: Choose voice (default: `af_heart`)
- `--warm-repeats`: Number of warmup iterations (default: 5)
- `--out`: Output JSON path

### Benchmarking CoreML

```bash
# Using Apple Neural Engine (ANE) - FASTEST
python -m hypnogen.benchmarks.bench_tts_only \
  --provider coreml \
  --compute-units ALL \
  --voice af_heart \
  --out .sisyphus/benchmarks/tts_coreml_ane.json

# Using CPU + GPU (fallback if ANE unavailable)
python -m hypnogen.benchmarks.bench_tts_only \
  --provider coreml \
  --compute-units CPU_AND_GPU \
  --voice af_heart \
  --out .sisyphus/benchmarks/tts_coreml_cpu_gpu.json

# CPU Only (slowest, for debugging)
python -m hypnogen.benchmarks.bench_tts_only \
  --provider coreml \
  --compute-units CPU_ONLY \
  --voice af_heart \
  --out .sisyphus/benchmarks/tts_coreml_cpu.json
```

**Compute Units Options:**
- `ALL` - Use all available compute units (ANE, GPU, CPU) - **Recommended**
- `CPU_AND_GPU` - Use CPU and GPU only (no ANE)
- `CPU_ONLY` - CPU only (slowest, for debugging)

---

## Comparing Results

### CLI Comparison

```bash
python hypnogen/benchmarks/compare_tts_results.py \
  .sisyphus/benchmarks/tts_pytorch.json \
  .sisyphus/benchmarks/tts_coreml_ane.json
```

This outputs an ASCII table showing RTF improvements:

```
================================================================================
TTS BENCHMARK COMPARISON
================================================================================
Baseline:  pytorch (compute_units=N/A) @ 2026-02-11T10:30:00
Optimized: coreml (compute_units=ALL) @ 2026-02-11T10:35:00

Case                      Cold RTF  Cold RTF  Change  Warm RTF  Warm RTF  Change
                          (baseline) (optimized)          (baseline) (optimized)
-----------------------------------------------------------------------------------------
short_relaxation             0.523      2.341  +347.4%      0.489      2.298  +369.9%
medium_confidence            0.412      1.987  +382.2%      0.398      1.923  +383.2%
long_sleep                   0.298      1.654  +455.0%      0.287      1.612  +461.6%
-----------------------------------------------------------------------------------------
AVERAGE                                        +394.9%                              +404.9%
```

### Generate Markdown Report

```bash
python hypnogen/benchmarks/compare_tts_results.py \
  .sisyphus/benchmarks/tts_pytorch.json \
  .sisyphus/benchmarks/tts_coreml_ane.json \
  --report .sisyphus/benchmarks/comparison_report.md
```

---

## Pipeline Benchmarks

For end-to-end benchmarking of the entire Hypnogen pipeline (script parsing → TTS → binaural bed → mixing):

```bash
# Quick benchmark (~60s session)
python benchmark_pipeline.py --scale short --tag baseline

# Full benchmark (~15-18 min session)
python benchmark_pipeline.py --scale large --tag baseline

# With TTS warmup first
python benchmark_pipeline.py --scale short --warmup --tag baseline
```

Output is saved to `.sisyphus/benchmarks/{tag}_{scale}_{timestamp}.json`

---

## Full CoreML Benchmark

For benchmarking the complete CoreML-only TTS pipeline (no PyTorch F0Ntrain):

```bash
python benchmark_full_coreml.py
```

This tests:
1. Duration model inference (CoreML)
2. Alignment matrix construction
3. Synthesizer inference (CoreML)

Output includes RTF and saves audio to `/tmp/test_full_coreml.wav`

---

## Interpreting Results

### Expected Performance (Apple Silicon M1-M4)

| Provider | Cold RTF | Warm RTF | Notes |
|----------|----------|----------|-------|
| PyTorch | ~0.3-0.5 | ~0.3-0.5 | CPU-based |
| CoreML (CPU_ONLY) | ~0.5-1.0 | ~0.5-1.0 | Fallback |
| CoreML (CPU_AND_GPU) | ~1.5-2.5 | ~1.5-2.5 | GPU accelerated |
| CoreML (ALL/ANE) | ~2.0-4.0+ | ~2.0-4.0+ | Neural Engine |

### Key Metrics

- **Cold RTF**: First run (includes model loading, compilation)
- **Warm RTF**: Subsequent runs (cached models, no recompilation)
- **Sanity Checks**: Validates audio output quality

### Common Issues

1. **Low RTF on CoreML**: Ensure models are compiled and ANE is available
2. **Audio validation fails**: Check that TTS models are properly converted
3. **Memory issues**: Close other apps, ensure sufficient RAM

---

## Benchmark Corpus

The default corpus (`hypnogen/benchmarks/corpus/tts_corpus.json`) contains 3 test cases:

1. **short_relaxation** (~180 words) - Brief relaxation script
2. **medium_confidence** (~250 words) - Confidence building script
3. **long_sleep** (~380 words) - Sleep induction with countdown

You can create custom corpus files following the same JSON format.

---

## Hardware Notes

### Recommended: Mac with Apple Silicon

- M1/M2/M3/M4 chips have dedicated Neural Engine (ANE)
- CoreML with `compute_units=ALL` automatically uses ANE
- Best results on M3/M4 with unified memory

### PyTorch Baseline

- Runs on any Mac or Linux machine
- Uses CPU only (no GPU acceleration in current setup)
- Good baseline for comparison
