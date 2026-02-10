"""Compare two benchmark JSON results and report deltas.

Usage:
    python -m hypnogen.benchmarks.compare baseline.json current.json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def compare_results(
    baseline: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, Any]:
    """Compare two benchmark result dicts and return deltas.

    Args:
        baseline: The reference benchmark result.
        current: The new benchmark result to compare against baseline.

    Returns:
        Dict with:
            - total_sec: {baseline, current, delta, pct}
            - stages: {stage_name: {baseline, current, delta, pct}}
            - config_mismatch: bool (True if config hashes differ)
    """
    config_mismatch = baseline.get("config_hash") != current.get("config_hash")

    total_baseline = baseline["total_sec"]
    total_current = current["total_sec"]
    total_delta = total_current - total_baseline
    total_pct = (total_delta / total_baseline * 100) if total_baseline else 0.0

    stages_deltas: dict[str, dict[str, float]] = {}
    all_stage_names = set(baseline.get("stages", {}).keys()) | set(current.get("stages", {}).keys())

    for stage in sorted(all_stage_names):
        b_val = baseline.get("stages", {}).get(stage, 0.0)
        c_val = current.get("stages", {}).get(stage, 0.0)
        delta = c_val - b_val
        pct = (delta / b_val * 100) if b_val else 0.0
        stages_deltas[stage] = {
            "baseline": b_val,
            "current": c_val,
            "delta": delta,
            "pct": pct,
        }

    return {
        "total_sec": {
            "baseline": total_baseline,
            "current": total_current,
            "delta": total_delta,
            "pct": total_pct,
        },
        "stages": stages_deltas,
        "config_mismatch": config_mismatch,
    }


def format_comparison(deltas: dict[str, Any]) -> str:
    """Format comparison deltas as a human-readable string.

    Args:
        deltas: Output from compare_results().

    Returns:
        Multi-line string showing baseline, current, delta, and percent change.
    """
    lines: list[str] = []

    if deltas.get("config_mismatch"):
        lines.append("WARNING: config hashes differ — results may not be comparable")
        lines.append("")

    total = deltas["total_sec"]
    sign = "+" if total["delta"] >= 0 else ""
    lines.append(
        f"Total: {total['baseline']:.3f}s -> {total['current']:.3f}s "
        f"({sign}{total['delta']:.3f}s, {sign}{total['pct']:.1f}%)"
    )
    lines.append("")
    lines.append(f"{'Stage':>10s}  {'Baseline':>10s}  {'Current':>10s}  {'Delta':>10s}  {'Change':>8s}")
    lines.append("-" * 56)

    for stage, vals in deltas["stages"].items():
        sign = "+" if vals["delta"] >= 0 else ""
        lines.append(
            f"{stage:>10s}  {vals['baseline']:>10.3f}  {vals['current']:>10.3f}  "
            f"{sign}{vals['delta']:>9.3f}  {sign}{vals['pct']:>7.1f}%"
        )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare two hypnogen benchmark JSON results.",
    )
    parser.add_argument("baseline", help="Path to baseline JSON")
    parser.add_argument("current", help="Path to current JSON")
    args = parser.parse_args()

    with open(args.baseline) as f:
        baseline = json.load(f)
    with open(args.current) as f:
        current = json.load(f)

    deltas = compare_results(baseline, current)
    print(format_comparison(deltas))

    if deltas.get("config_mismatch"):
        sys.exit(2)


if __name__ == "__main__":
    main()
