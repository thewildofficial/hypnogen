# Hypnogen TTS Benchmark Guide

Benchmarks CoreML (Apple Neural Engine, 17x speedup) vs PyTorch TTS on Apple Silicon.

The CoreML models come from [mattmireles/kokoro-coreml](https://github.com/mattmireles/kokoro-coreml), a two-stage Duration + Decoder pipeline exported with fixed shapes for ANE acceleration. They're stored via Git LFS in the `vendor/kokoro-coreml` submodule.

## Prerequisites

- **macOS** with Apple Silicon (M1/M2/M3/M4)
- **Git LFS** installed: `brew install git-lfs && git lfs install`
- **uv** installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Python 3.12+**

## Quick Start

```bash
# 1. Clone repo with submodules + LFS
git clone --recurse-submodules https://github.com/thewildofficial/hypnogen.git
cd hypnogen
git checkout wop-benchmark

# 2. Pull LFS files (the CoreML .mlpackage weights)
cd vendor/kokoro-coreml && git lfs pull && cd ../..

# 3. Install dependencies (base + CoreML extras)
uv sync --group coreml

# 4. Copy CoreML models from vendor submodule
uv run python download_coreml_models.py

# 5. Run PyTorch benchmark
uv run python -m hypnogen.benchmarks.bench_tts_only \
  --provider pytorch \
  --out .sisyphus/benchmarks/tts_pytorch.json

# 6. Run CoreML benchmark
uv run python -m hypnogen.benchmarks.bench_tts_only \
  --provider coreml \
  --compute-units ALL \
  --out .sisyphus/benchmarks/tts_coreml.json

# 7. Compare
uv run python hypnogen/benchmarks/compare_tts_results.py \
  .sisyphus/benchmarks/tts_pytorch.json \
  .sisyphus/benchmarks/tts_coreml.json
```

---

## Getting CoreML Models

The benchmark needs 4 `.mlpackage` files in `coreml_models/`:

- `kokoro_duration.mlpackage` — Duration predictor (CPU/GPU)
- `kokoro_decoder_only_3s.mlpackage` — 3s audio decoder (ANE)
- `kokoro_decoder_only_5s.mlpackage` — 5s audio decoder (ANE)
- `kokoro_decoder_only_10s.mlpackage` — 10s audio decoder (ANE)

Each `.mlpackage` must contain `Data/com.apple.CoreML/weights/weight.bin` (the actual model weights).

### Copy from Vendor Submodule (Default)

The models live in `vendor/kokoro-coreml/coreml/` via Git LFS. The script copies them to `coreml_models/`:

```bash
# Make sure LFS files are pulled first
cd vendor/kokoro-coreml && git lfs pull && cd ../..

# Copy models (~468MB)
uv run python download_coreml_models.py
```

### Export from PyTorch (30-60 min)

Only needed if you want to re-export custom models:

```bash
cd vendor/kokoro-coreml
python export_duration.py                                    # -> coreml/kokoro_duration.mlpackage
python export_synthesizers.py --mode decoder --buckets 3s,5s,10s  # -> coreml/kokoro_decoder_only_*.mlpackage
cp -r coreml/kokoro_duration.mlpackage ../../coreml_models/
cp -r coreml/kokoro_decoder_only_*.mlpackage ../../coreml_models/
```

Requires: `pip install torch==2.6.0 coremltools==8.3.0 safetensors numpy==1.26.4`

---

## Understanding RTF

**RTF (Real-Time Factor)** = Audio duration / Processing time

| RTF | Meaning |
|-----|---------|
| 0.5 | Slow (2s to generate 1s audio) |
| 1.0 | Real-time |
| 4.0 | 4x faster than real-time |
| 17.0 | 17x faster (CoreML + ANE target) |

**Higher = Better**

---

## Expected Results

| Provider | Cold RTF | Warm RTF |
|----------|----------|----------|
| PyTorch | ~0.3-0.5 | ~0.3-0.5 |
| CoreML (ANE) | ~2.0-4.0+ | ~4.0-17.0+ |

**Speedup: 4-17x with CoreML + ANE** (varies by chip; M2 Ultra sees ~17x)

---

## Troubleshooting

**`coremltools` import error** → Run `uv sync --group coreml` (not just `uv sync`).

**"CoreML model not found"** → Run `uv run python download_coreml_models.py`. Check that `coreml_models/kokoro_duration.mlpackage/Data/com.apple.CoreML/weights/weight.bin` exists.

**"Vendor CoreML directory not found"** → The `vendor/kokoro-coreml` submodule isn't initialized. Run `git submodule update --init --recursive`.

**"weight.bin is missing (Git LFS not pulled)"** → The submodule has LFS pointer files instead of actual weights. Run `cd vendor/kokoro-coreml && git lfs pull`.

**Low RTF on first run** → First ANE compile takes 10-30 min. Subsequent runs use cached compilation. Check Activity Monitor for ANE usage.

**Memory issues** → Close other apps. Each model uses ~200MB at runtime.
