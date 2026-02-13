#!/usr/bin/env python3
"""Copy CoreML models from vendor/kokoro-coreml into coreml_models/.

The models are stored via Git LFS in the vendor/kokoro-coreml submodule
(https://github.com/mattmireles/kokoro-coreml). This script copies the
4 required .mlpackage directories into coreml_models/ where the benchmark
and CoreMLProvider expect them.

Usage:
    uv run python download_coreml_models.py
    uv run python download_coreml_models.py --out-dir ./models
"""

import argparse
import shutil
import sys
from pathlib import Path

VENDOR_COREML_DIR = Path(__file__).resolve().parent / "vendor" / "kokoro-coreml" / "coreml"

REQUIRED_MODELS = [
    "kokoro_duration.mlpackage",
    "kokoro_decoder_only_3s.mlpackage",
    "kokoro_decoder_only_5s.mlpackage",
    "kokoro_decoder_only_10s.mlpackage",
]


def _has_weights(model_path: Path) -> bool:
    return model_path.exists() and any(model_path.rglob("weight.bin"))


def copy_models(out_dir: Path, vendor_dir: Path = VENDOR_COREML_DIR) -> bool:
    out_dir = Path(out_dir)

    already_present = all(_has_weights(out_dir / name) for name in REQUIRED_MODELS)
    if already_present:
        print(f"All {len(REQUIRED_MODELS)} required models already present in {out_dir}")
        return True

    if not vendor_dir.exists():
        print(f"Vendor CoreML directory not found: {vendor_dir}")
        print()
        print("Make sure you cloned with submodules:")
        print("  git submodule update --init --recursive")
        print()
        print("Or clone fresh:")
        print("  git clone --recurse-submodules <repo-url>")
        return False

    missing_in_vendor = []
    lfs_stubs = []
    for name in REQUIRED_MODELS:
        src = vendor_dir / name
        if not src.exists():
            missing_in_vendor.append(name)
        elif not _has_weights(src):
            lfs_stubs.append(name)

    if missing_in_vendor:
        print(f"Models missing from vendor submodule ({vendor_dir}):")
        for name in missing_in_vendor:
            print(f"  - {name}")
        return False

    if lfs_stubs:
        print("Models exist but weight.bin is missing (Git LFS not pulled):")
        for name in lfs_stubs:
            print(f"  - {name}")
        print()
        print("Pull LFS files with:")
        print(f"  cd {vendor_dir.parent} && git lfs pull")
        return False

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Copying CoreML models from {vendor_dir}")
    print(f"Destination: {out_dir.absolute()}")
    print()

    ok = True
    for name in REQUIRED_MODELS:
        src = vendor_dir / name
        dst = out_dir / name

        if _has_weights(dst):
            print(f"  {name}: already present, skipping")
            continue

        if dst.exists():
            shutil.rmtree(dst)

        print(f"  {name}: copying...", end=" ", flush=True)
        try:
            shutil.copytree(src, dst)
            if _has_weights(dst):
                size_mb = sum(
                    f.stat().st_size for f in dst.rglob("*") if f.is_file()
                ) / (1024 * 1024)
                print(f"ok ({size_mb:.0f} MB)")
            else:
                print("FAILED (no weight.bin after copy)")
                ok = False
        except Exception as e:
            print(f"FAILED ({e})")
            ok = False

    if ok:
        print(f"\nAll models copied to {out_dir}")
    else:
        print("\nSome models failed to copy.")

    return ok


def main():
    parser = argparse.ArgumentParser(
        description="Copy CoreML models from vendor/kokoro-coreml to coreml_models/"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("coreml_models"),
        help="Output directory (default: coreml_models/)",
    )
    parser.add_argument(
        "--vendor-dir",
        type=Path,
        default=VENDOR_COREML_DIR,
        help="Source vendor/kokoro-coreml/coreml directory",
    )
    args = parser.parse_args()

    success = copy_models(args.out_dir, args.vendor_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
