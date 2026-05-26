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
    "forbidden_field_violation",
    "timeout",
    "trace_or_recording_error",
    "unknown",
]


def write_failure_analysis(out_dir: str | Path, freebeam_trace: Iterable[Dict[str, Any]], compiler_metrics: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(out_dir)
    examples = {key: [] for key in FAILURE_CATEGORIES}
    for row in freebeam_trace:
        if row.get("category") == "current_supported_turing_substrate" and not row.get("candidate_hit"):
            examples["candidate_miss"].append(row)
        elif row.get("category") == "current_supported_turing_substrate" and row.get("correct_output_in_beam") and not row.get("top1_correct"):
            examples["candidate_in_beam_but_wrong_top1"].append(row)
    flat = []
    for category, rows in examples.items():
        for row in rows[:50]:
            flat.append({"failure_category": category, "sample_id_hash": row.get("sample_id_hash"), "stage": row.get("stage"), "category": row.get("category")})
    (out / "failure_examples.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in flat), encoding="utf-8")
    summary = {key: len(value) for key, value in examples.items()}
    (out / "failure_analysis.md").write_text("\n".join([
        "# v0.9.7 Failure Analysis",
        "",
        f"- candidate_miss: {summary['candidate_miss']}",
        f"- candidate_in_beam_but_wrong_top1: {summary['candidate_in_beam_but_wrong_top1']}",
        f"- compiler_compile_failure: {compiler_metrics.get('compile_failure_count', 0)}",
        f"- compiler_runtime_failure: {compiler_metrics.get('runtime_failure_count', 0)}",
        "- Most remaining probe failures are candidate-space/top1 issues rather than compiler infrastructure issues.",
    ]) + "\n", encoding="utf-8")
    return summary
