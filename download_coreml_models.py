#!/usr/bin/env python3
"""Download CoreML models for Kokoro TTS from HuggingFace.

This script automatically downloads pre-converted CoreML models so contributors
don't need to manually export them (which takes 30-60 minutes).

Usage:
    python download_coreml_models.py              # Download to default location
    python download_coreml_models.py --out-dir ./models  # Custom location
"""

import argparse
import sys
from pathlib import Path


def download_models(out_dir: Path, repo_id: str = "FluidInference/kokoro-82m-coreml") -> bool:
    """Download CoreML models from HuggingFace.
    
    Args:
        out_dir: Directory to save models
        repo_id: HuggingFace repo to download from
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from huggingface_hub import hf_hub_download, list_repo_files
    except ImportError:
        print("❌ huggingface-hub not installed.")
        print("   Install with: uv pip install huggingface-hub")
        return False
    
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📦 Downloading CoreML models from {repo_id}")
    print(f"   Destination: {out_dir.absolute()}")
    print()
    
    try:
        # List files in the repo
        files = list_repo_files(repo_id)
        
        # Find .mlpackage directories (they appear as files with / in the path)
        mlpackage_files = [f for f in files if '.mlpackage' in f]
        
        if not mlpackage_files:
            print("⚠️  No .mlpackage files found in repository")
            return False
        
        print(f"   Found {len(mlpackage_files)} model files/directories")
        
        # Download each file
        downloaded = 0
        for file_path in mlpackage_files:
            try:
                local_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=file_path,
                    local_dir=out_dir,
                    local_dir_use_symlinks=False
                )
                print(f"   ✅ {file_path}")
                downloaded += 1
            except Exception as e:
                print(f"   ⚠️  {file_path} - {e}")
        
        print()
        print(f"✅ Downloaded {downloaded} files to {out_dir}")
        
        # Check what we got
        duration_model = out_dir / "kokoro_duration.mlpackage"
        decoder_models = list(out_dir.glob("kokoro_decoder_only_*.mlpackage"))
        
        print()
        print("📋 Model status:")
        print(f"   Duration model: {'✅ Found' if duration_model.exists() else '❌ Missing'}")
        print(f"   Decoder models: {len(decoder_models)} found")
        for dm in decoder_models:
            print(f"      - {dm.name}")
        
        return duration_model.exists() and len(decoder_models) > 0
        
    except Exception as e:
        print(f"❌ Error downloading models: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download CoreML models for Kokoro TTS"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("coreml_models"),
        help="Output directory for models (default: coreml_models/)"
    )
    parser.add_argument(
        "--repo",
        default="FluidInference/kokoro-82m-coreml",
        help="HuggingFace repo to download from"
    )
    
    args = parser.parse_args()
    
    success = download_models(args.out_dir, args.repo)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
