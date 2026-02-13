# Hypnogen TTS Benchmark Guide

Complete end-to-end guide for benchmarking CoreML (Apple Neural Engine) vs PyTorch TTS implementations.

## Prerequisites

- **macOS** with Apple Silicon (M1/M2/M3/M4)
- **uv** installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Python 3.12+**

## Quick Start

```bash
# 1. Clone repo
git clone https://github.com/thewildofficial/hypnogen.git
cd hypnogen
git checkout wop-benchmark

# 2. Install dependencies
uv sync

# 3. Run PyTorch benchmark
uv run python -m hypnogen.benchmarks.bench_tts_only \
  --provider pytorch \
  --out .sisyphus/benchmarks/tts_pytorch.json

# 4. Get CoreML models (see below), then run:
uv run python -m hypnogen.benchmarks.bench_tts_only \
  --provider coreml \
  --compute-units ALL \
  --out .sisyphus/benchmarks/tts_coreml.json

# 5. Compare
uv run python hypnogen/benchmarks/compare_tts_results.py \
  .sisyphus/benchmarks/tts_pytorch.json \
  .sisyphus/benchmarks/tts_coreml.json
```

---

## Getting CoreML Models

Models are **not included** in git (too large). Three options:

### Option A: Download from HuggingFace (Recommended - Fast)

Pre-converted CoreML models are available on HuggingFace:

```bash
# Install huggingface-cli
uv pip install huggingface-hub

# Download the models
mkdir -p coreml_models
cd coreml_models

# Download duration model
uv run huggingface-cli download FluidInference/kokoro-82m-coreml --include "*.mlpackage" --local-dir .

# Or download specific files manually from:
# https://huggingface.co/FluidInference/kokoro-82m-coreml
```

Required files:
- `kokoro_duration.mlpackage`
- `kokoro_decoder_only_3s.mlpackage` (or 5s/10s variants)

### Option B: Use FluidAudio CLI (Auto-download)

The FluidAudio Swift CLI tool auto-downloads models on first run:

```bash
# Install and run (downloads models automatically)
swift run fluidaudio tts "Hello" --output test.wav --voice af_heart

# Models cached to: ~/Library/Caches/FluidAudio/
# Copy them to your coreml_models/ directory
```

### Option C: Export from PyTorch (30-60 min)

If you need custom models or the above options don't work:

```bash
cd vendor/kokoro-coreml

# Download base model (~300MB)
uv run python -c "from kokoro import KModel; KModel()"

# Export CoreML models
uv run python export_duration.py --out-dir ../../coreml_models
uv run python export_synthesizers.py --out-dir ../../coreml_models

cd ../..
```

---

## Understanding RTF

**RTF (Real-Time Factor)** = Audio duration / Processing time

| RTF | Performance |
|-----|-------------|
| 0.5 | Slow (2s to generate 1s audio) |
| 1.0 | Real-time (1s to generate 1s audio) |
| 2.0 | Fast (0.5s to generate 1s audio) |
| 4.0 | Very fast (0.25s to generate 1s audio) |

**Higher = Better**

---

## Expected Results

| Provider | Cold RTF | Warm RTF |
|----------|----------|----------|
| PyTorch | ~0.3-0.5 | ~0.3-0.5 |
| CoreML (ANE) | ~2.0-4.0+ | ~2.0-4.0+ |

**Speedup: 4-10x with CoreML + ANE**

---

## Troubleshooting

**"CoreML model not found"** → Models not set up. See [Getting CoreML Models](#getting-coreml-models).

**Low RTF** → First ANE compile takes 10-30 min. Check Activity Monitor for ANE usage.

**Memory issues** → Close other apps during benchmark.
