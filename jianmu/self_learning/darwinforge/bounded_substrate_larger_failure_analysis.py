from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable


FAILURE_CATEGORIES = [
    "candidate_miss",
    "candidate_in_beam_but_wrong_top1",
    "compiler_compile_failure",
    "compiler_runtime_failure",
    "wrong_stdout",
    "boundary_false_accept",
    "boundary_compiler_misroute",
    "permission_error",
    "cleanup_failure",
    "forbidden_field_violation",
    "timeout",
    "trace_or_recording_error",
    "unknown",
]


def write_larger_failure_analysis(out_dir: str | Path, freebeam_trace: Iterable[Dict[str, Any]], compiler_metrics: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    counts = {category: 0 for category in FAILURE_CATEGORIES}
    examples = []
    for row in freebeam_trace:
        category = ""
        if row.get("category") == "current_supported_turing_substrate" and not row.get("candidate_hit"):
            category = "candidate_miss"
        elif row.get("category") == "current_supported_turing_substrate" and row.get("correct_output_in_beam") and not row.get("top1_correct"):
            category = "candidate_in_beam_but_wrong_top1"
        elif row.get("accepted_supported") and row.get("category") != "current_supported_turing_substrate":
            category = "boundary_false_accept"
        if category:
            counts[category] += 1
            if sum(1 for item in examples if item["failure_category"] == category) < 50:
                examples.append({
                    "failure_category": category,
                    "sample_id_hash": row.get("sample_id_hash"),
                    "stage": row.get("stage"),
                    "category": row.get("category"),
                    "notes": "larger rerun per-sample trace failure",
                })
    if compiler_metrics.get("compile_failure_count", 0):
        counts["compiler_compile_failure"] = compiler_metrics["compile_failure_count"]
    if compiler_metrics.get("runtime_failure_count", 0):
        counts["compiler_runtime_failure"] = compiler_metrics["runtime_failure_count"]
    if compiler_metrics.get("permission_error_count", 0):
        counts["permission_error"] = compiler_metrics["permission_error_count"]
    if compiler_metrics.get("cleanup_failure_count", 0):
        counts["cleanup_failure"] = compiler_metrics["cleanup_failure_count"]
    if compiler_metrics.get("timeout_count", 0):
        counts["timeout"] = compiler_metrics["timeout_count"]
    (out / "failure_examples.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in examples), encoding="utf-8")
    lines = [
        "# Bounded Substrate Larger Failure Analysis",
        "",
        "Failures are reported from per-sample free-beam trace and clean MSVC compiler validation metrics.",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in counts.items() if value)
    if not any(counts.values()):
        lines.append("- no failures recorded")
    (out / "failure_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"failure_category_counts": counts, "example_count": len(examples)}

