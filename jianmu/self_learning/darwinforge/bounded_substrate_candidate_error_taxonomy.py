from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.bounded_substrate_training_state import SUPPORTED_STAGES


FAILURE_TYPES = [
    "candidate_miss",
    "candidate_in_beam_but_wrong_top1",
    "top1_compiler_wrong",
    "compiler_compile_failure",
    "compiler_runtime_failure",
    "boundary_false_accept",
    "boundary_compiler_misroute",
    "forbidden_field_violation",
    "trace_or_recording_error",
    "unknown",
]


def classify_candidate_error(row: Dict[str, Any]) -> str:
    if row.get("forbidden_field_access_count", 0):
        return "forbidden_field_violation"
    if row.get("category") != "current_supported_turing_substrate":
        return "boundary_false_accept" if row.get("accepted_supported") else ""
    if not row.get("candidate_hit"):
        return "candidate_miss"
    if row.get("correct_output_in_beam") and not row.get("top1_correct"):
        return "candidate_in_beam_but_wrong_top1"
    if row.get("candidate_hit") and not row.get("correct_output_in_beam"):
        return "top1_compiler_wrong"
    return ""


def run_candidate_error_taxonomy(source_records: str | Path, output_records: str | Path, max_examples_per_type: int = 50) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    traces = list(_load_trace(Path(source_records) / "heldout_freebeam_trace.jsonl"))
    if not traces:
        traces = list(_load_trace(Path(source_records) / "freebeam_after_trace.jsonl"))
    by_stage: Dict[str, Dict[str, Any]] = {}
    examples: List[Dict[str, Any]] = []
    example_counts: Dict[str, int] = defaultdict(int)
    total_failures = 0
    total_supported = 0
    global_counts = {key: 0 for key in FAILURE_TYPES}
    for stage in SUPPORTED_STAGES:
        rows = [row for row in traces if row.get("stage") == stage and row.get("category") == "current_supported_turing_substrate"]
        counts = {key: 0 for key in FAILURE_TYPES}
        for row in rows:
            total_supported += 1
            kind = classify_candidate_error(row)
            if not kind:
                continue
            counts[kind] += 1
            global_counts[kind] += 1
            total_failures += 1
            if example_counts[kind] < max_examples_per_type:
                examples.append({
                    "failure_type": kind,
                    "sample_id_hash": row.get("sample_id_hash"),
                    "stage": row.get("stage"),
                    "category": row.get("category"),
                    "candidate_hit": row.get("candidate_hit"),
                    "correct_output_in_beam": row.get("correct_output_in_beam"),
                    "top1_correct": row.get("top1_correct"),
                })
                example_counts[kind] += 1
        dominant = max(counts, key=counts.get) if rows else "unknown"
        if counts.get(dominant, 0) == 0:
            dominant = "none"
        by_stage[stage] = {
            "stage": stage,
            "sample_count": len(rows),
            "candidate_miss_count": counts["candidate_miss"],
            "candidate_in_beam_but_wrong_top1_count": counts["candidate_in_beam_but_wrong_top1"],
            "top1_compiler_wrong_count": counts["top1_compiler_wrong"],
            "compiler_failure_count": counts["compiler_compile_failure"] + counts["compiler_runtime_failure"],
            "boundary_false_accept_count": counts["boundary_false_accept"],
            "unknown_count": counts["unknown"],
            "dominant_failure_type": dominant,
            "candidate_miss_rate": _rate(counts["candidate_miss"], len(rows)),
            "in_beam_wrong_top1_rate": _rate(counts["candidate_in_beam_but_wrong_top1"], len(rows)),
            "top1_wrong_rate": _rate(len(rows) - sum(1 for row in rows if row.get("top1_correct")), len(rows)),
        }
    total_candidate_miss = global_counts["candidate_miss"]
    total_in_beam_wrong = global_counts["candidate_in_beam_but_wrong_top1"]
    dominant_failure_type = max(global_counts, key=global_counts.get) if global_counts else "unknown"
    result = {
        "candidate_error_taxonomy_completed": True,
        "sample_count": total_supported,
        "failure_count": total_failures,
        "global_failure_counts": global_counts,
        "candidate_miss_rate": _rate(total_candidate_miss, total_supported),
        "in_beam_wrong_top1_rate": _rate(total_in_beam_wrong, total_supported),
        "dominant_failure_type": dominant_failure_type,
        "by_stage": by_stage,
    }
    _write_json(out / "candidate_error_taxonomy.json", result)
    (out / "candidate_error_examples.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in examples), encoding="utf-8")
    return result


def _load_trace(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _rate(num: int, den: int) -> float:
    return round(num / den, 6) if den else 0.0


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

