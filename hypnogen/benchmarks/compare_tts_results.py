"""Compare two TTS benchmark JSON results and generate a report.

Usage:
    python hypnogen/benchmarks/compare_tts_results.py \\
        .sisyphus/benchmarks/tts_only_coreml_cpu_gpu.json \\
        .sisyphus/benchmarks/tts_only_coreml_all.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_benchmark(path: Path) -> dict[str, Any]:
    """Load a TTS benchmark JSON file with graceful error handling."""
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)


def extract_rtf_metrics(data: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Extract RTF metrics per case from benchmark data.

    Returns:
        Dict mapping case_id -> {cold_rtf, warm_rtf, cold_wall_sec, warm_wall_sec,
                                  audio_duration_sec}
    """
    metrics: dict[str, dict[str, float]] = {}
    for run in data.get("runs", []):
        case_id = run["case_id"]
        cold = run.get("cold", {})
        warm = run.get("warm", {})
        metrics[case_id] = {
            "cold_rtf": cold.get("rtf", 0.0),
            "warm_rtf": warm.get("mean_rtf", 0.0),
            "cold_wall_sec": cold.get("wall_time_sec", 0.0),
            "warm_wall_sec": warm.get("mean_wall_time_sec", 0.0),
            "audio_duration_sec": cold.get("audio_duration_sec", 0.0),
        }
    return metrics


def compute_improvement(baseline_rtf: float, optimized_rtf: float) -> float:
    """Compute improvement percentage.

    Formula: (RTF_optimized - RTF_baseline) / RTF_baseline * 100%

    A positive value means the optimized version produces audio faster
    (higher RTF = more audio per unit wall-clock time = better).
    """
    if baseline_rtf == 0.0:
        return 0.0
    return (optimized_rtf - baseline_rtf) / baseline_rtf * 100.0


def compare_tts_results(
    baseline: dict[str, Any],
    optimized: dict[str, Any],
) -> dict[str, Any]:
    """Compare two TTS benchmark result dicts and return structured deltas.

    Returns:
        Dict with per-case comparisons and overall summary.
    """
    baseline_metrics = extract_rtf_metrics(baseline)
    optimized_metrics = extract_rtf_metrics(optimized)

    all_cases = sorted(set(baseline_metrics) | set(optimized_metrics))

    cases: list[dict[str, Any]] = []
    for case_id in all_cases:
        b = baseline_metrics.get(case_id, {})
        o = optimized_metrics.get(case_id, {})

        entry: dict[str, Any] = {
            "case_id": case_id,
            "baseline_cold_rtf": b.get("cold_rtf", 0.0),
            "optimized_cold_rtf": o.get("cold_rtf", 0.0),
            "cold_improvement_pct": compute_improvement(
                b.get("cold_rtf", 0.0), o.get("cold_rtf", 0.0)
            ),
            "baseline_warm_rtf": b.get("warm_rtf", 0.0),
            "optimized_warm_rtf": o.get("warm_rtf", 0.0),
            "warm_improvement_pct": compute_improvement(
                b.get("warm_rtf", 0.0), o.get("warm_rtf", 0.0)
            ),
            "baseline_cold_wall_sec": b.get("cold_wall_sec", 0.0),
            "optimized_cold_wall_sec": o.get("cold_wall_sec", 0.0),
            "baseline_warm_wall_sec": b.get("warm_wall_sec", 0.0),
            "optimized_warm_wall_sec": o.get("warm_wall_sec", 0.0),
            "in_baseline": case_id in baseline_metrics,
            "in_optimized": case_id in optimized_metrics,
        }
        cases.append(entry)

    shared = [c for c in cases if c["in_baseline"] and c["in_optimized"]]
    avg_cold_improvement = (
        sum(c["cold_improvement_pct"] for c in shared) / len(shared)
        if shared
        else 0.0
    )
    avg_warm_improvement = (
        sum(c["warm_improvement_pct"] for c in shared) / len(shared)
        if shared
        else 0.0
    )

    return {
        "baseline_config": baseline.get("config", {}),
        "optimized_config": optimized.get("config", {}),
        "baseline_timestamp": baseline.get("timestamp", "unknown"),
        "optimized_timestamp": optimized.get("timestamp", "unknown"),
        "cases": cases,
        "avg_cold_improvement_pct": avg_cold_improvement,
        "avg_warm_improvement_pct": avg_warm_improvement,
    }


def format_table(comparison: dict[str, Any]) -> str:
    """Format comparison as a human-readable ASCII table."""
    lines: list[str] = []

    b_cfg = comparison["baseline_config"]
    o_cfg = comparison["optimized_config"]
    lines.append("=" * 80)
    lines.append("TTS BENCHMARK COMPARISON")
    lines.append("=" * 80)
    lines.append(
        f"Baseline:  {b_cfg.get('provider', '?')} "
        f"(compute_units={b_cfg.get('compute_units', 'N/A')}) "
        f"@ {comparison['baseline_timestamp']}"
    )
    lines.append(
        f"Optimized: {o_cfg.get('provider', '?')} "
        f"(compute_units={o_cfg.get('compute_units', 'N/A')}) "
        f"@ {comparison['optimized_timestamp']}"
    )
    lines.append("")

    hdr = (
        f"{'Case':<25s}  "
        f"{'Cold RTF':>10s}  {'Cold RTF':>10s}  {'Change':>8s}  "
        f"{'Warm RTF':>10s}  {'Warm RTF':>10s}  {'Change':>8s}"
    )
    sub = (
        f"{'':25s}  "
        f"{'(baseline)':>10s}  {'(optimized)':>10s}  {'':>8s}  "
        f"{'(baseline)':>10s}  {'(optimized)':>10s}  {'':>8s}"
    )
    lines.append(hdr)
    lines.append(sub)
    lines.append("-" * len(hdr))

    for c in comparison["cases"]:
        flag = ""
        if not c["in_baseline"]:
            flag = " [NEW]"
        elif not c["in_optimized"]:
            flag = " [MISSING]"

        cold_sign = "+" if c["cold_improvement_pct"] >= 0 else ""
        warm_sign = "+" if c["warm_improvement_pct"] >= 0 else ""

        line = (
            f"{c['case_id']:<25s}  "
            f"{c['baseline_cold_rtf']:>10.3f}  "
            f"{c['optimized_cold_rtf']:>10.3f}  "
            f"{cold_sign}{c['cold_improvement_pct']:>6.1f}%  "
            f"{c['baseline_warm_rtf']:>10.3f}  "
            f"{c['optimized_warm_rtf']:>10.3f}  "
            f"{warm_sign}{c['warm_improvement_pct']:>6.1f}%"
            f"{flag}"
        )
        lines.append(line)

    lines.append("-" * len(hdr))

    avg_cold_sign = "+" if comparison["avg_cold_improvement_pct"] >= 0 else ""
    avg_warm_sign = "+" if comparison["avg_warm_improvement_pct"] >= 0 else ""
    lines.append(
        f"{'AVERAGE':<25s}  "
        f"{'':>10s}  {'':>10s}  "
        f"{avg_cold_sign}{comparison['avg_cold_improvement_pct']:>6.1f}%  "
        f"{'':>10s}  {'':>10s}  "
        f"{avg_warm_sign}{comparison['avg_warm_improvement_pct']:>6.1f}%"
    )
    lines.append("")

    return "\n".join(lines)


def generate_markdown_report(
    comparison: dict[str, Any],
    baseline_path: str,
    optimized_path: str,
) -> str:
    """Generate a Markdown report from comparison data."""
    lines: list[str] = []

    lines.append("# TTS Benchmark Comparison Report")
    lines.append("")

    b_cfg = comparison["baseline_config"]
    o_cfg = comparison["optimized_config"]
    lines.append("## Configuration")
    lines.append("")
    lines.append("| | Baseline | Optimized |")
    lines.append("|---|---|---|")
    lines.append(
        f"| **File** | `{baseline_path}` | `{optimized_path}` |"
    )
    lines.append(
        f"| **Provider** | {b_cfg.get('provider', 'N/A')} "
        f"| {o_cfg.get('provider', 'N/A')} |"
    )
    lines.append(
        f"| **Compute Units** | {b_cfg.get('compute_units', 'N/A')} "
        f"| {o_cfg.get('compute_units', 'N/A')} |"
    )
    lines.append(
        f"| **Voice** | {b_cfg.get('voice', 'N/A')} "
        f"| {o_cfg.get('voice', 'N/A')} |"
    )
    lines.append(
        f"| **Timestamp** | {comparison['baseline_timestamp']} "
        f"| {comparison['optimized_timestamp']} |"
    )
    lines.append("")

    lines.append("## RTF Comparison")
    lines.append("")
    lines.append(
        "| Case | Cold RTF (base) | Cold RTF (opt) | Cold Change "
        "| Warm RTF (base) | Warm RTF (opt) | Warm Change |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|")

    for c in comparison["cases"]:
        cold_sign = "+" if c["cold_improvement_pct"] >= 0 else ""
        warm_sign = "+" if c["warm_improvement_pct"] >= 0 else ""

        note = ""
        if not c["in_baseline"]:
            note = " *NEW*"
        elif not c["in_optimized"]:
            note = " *MISSING*"

        lines.append(
            f"| {c['case_id']}{note} "
            f"| {c['baseline_cold_rtf']:.3f} "
            f"| {c['optimized_cold_rtf']:.3f} "
            f"| {cold_sign}{c['cold_improvement_pct']:.1f}% "
            f"| {c['baseline_warm_rtf']:.3f} "
            f"| {c['optimized_warm_rtf']:.3f} "
            f"| {warm_sign}{c['warm_improvement_pct']:.1f}% |"
        )

    avg_cold_sign = "+" if comparison["avg_cold_improvement_pct"] >= 0 else ""
    avg_warm_sign = "+" if comparison["avg_warm_improvement_pct"] >= 0 else ""
    lines.append(
        f"| **AVERAGE** | | "
        f"| **{avg_cold_sign}{comparison['avg_cold_improvement_pct']:.1f}%** "
        f"| | "
        f"| **{avg_warm_sign}{comparison['avg_warm_improvement_pct']:.1f}%** |"
    )
    lines.append("")

    avg_warm = comparison["avg_warm_improvement_pct"]
    if avg_warm > 5:
        verdict = "Significant improvement in warm RTF throughput."
    elif avg_warm > 0:
        verdict = "Marginal improvement in warm RTF throughput."
    elif avg_warm > -5:
        verdict = "No significant change in warm RTF throughput."
    else:
        verdict = "Regression detected in warm RTF throughput."

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Average cold RTF change**: {avg_cold_sign}{comparison['avg_cold_improvement_pct']:.1f}%")
    lines.append(f"- **Average warm RTF change**: {avg_warm_sign}{comparison['avg_warm_improvement_pct']:.1f}%")
    lines.append(f"- **Verdict**: {verdict}")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare two TTS benchmark JSON results and generate a report.",
    )
    parser.add_argument("baseline", help="Path to baseline TTS benchmark JSON")
    parser.add_argument("optimized", help="Path to optimized TTS benchmark JSON")
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Output path for Markdown report (default: stdout only)",
    )
    args = parser.parse_args()

    baseline_path = Path(args.baseline)
    optimized_path = Path(args.optimized)

    baseline = load_benchmark(baseline_path)
    optimized = load_benchmark(optimized_path)

    comparison = compare_tts_results(baseline, optimized)

    print(format_table(comparison))

    md_report = generate_markdown_report(comparison, args.baseline, args.optimized)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(md_report)
        print(f"Markdown report saved to: {args.report}")
    else:
        print("--- Markdown Report ---")
        print(md_report)


if __name__ == "__main__":
    main()
