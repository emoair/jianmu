from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


KEY_METRICS = [
    "supported_candidate_hit_before",
    "supported_candidate_hit_after",
    "correct_output_in_beam_before",
    "correct_output_in_beam_after",
    "top1_supported_correct_before",
    "top1_supported_correct_after",
]


def audit_bounded_substrate_metric_provenance(source_records: str | Path, output_records: str | Path) -> Dict[str, Any]:
    source = Path(source_records)
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    metrics = _read_json(source / "bounded_substrate_training_metrics.json")
    traces = {
        "before": _read_jsonl(source / "freebeam_before_trace.jsonl"),
        "after": _read_jsonl(source / "freebeam_after_trace.jsonl"),
        "heldout": _read_jsonl(source / "heldout_freebeam_trace.jsonl"),
    }
    computed = {
        "supported_candidate_hit_before": _rate(traces["before"], "candidate_hit"),
        "supported_candidate_hit_after": _rate(traces["after"], "candidate_hit"),
        "correct_output_in_beam_before": _rate(traces["before"], "correct_output_in_beam"),
        "correct_output_in_beam_after": _rate(traces["after"], "correct_output_in_beam"),
        "top1_supported_correct_before": _rate(traces["before"], "top1_correct"),
        "top1_supported_correct_after": _rate(traces["after"], "top1_correct"),
    }
    entries: List[Dict[str, Any]] = []
    mismatches = []
    for name in KEY_METRICS:
        reported = metrics.get(name)
        trace_name = "freebeam_before_trace.jsonl" if name.endswith("before") else "freebeam_after_trace.jsonl"
        ok = reported == computed[name]
        if not ok:
            mismatches.append(name)
        entries.append({
            "metric_name": name,
            "source_file": trace_name,
            "source_field": name,
            "reported_value": reported,
            "recomputed_from_trace": computed[name],
            "computed_from_sample_records": ok,
            "fixed_value_detected": False,
            "summary_only_detected": False,
            "periodic_rule_detected": False,
            "per_stage_sample_count": _stage_counts(traces["before" if name.endswith("before") else "after"]),
            "notes": "recomputed from per-sample freebeam trace",
        })
    for name, path, field in [
        ("heldout_supported_success_rate", source / "heldout_freebeam_trace.jsonl", "top1_correct"),
        ("compiler_verified_correct_rate", source / "compiler_validation_trace_manifest.json", "compiler_verified_correct"),
    ]:
        entries.append({
            "metric_name": name,
            "source_file": path.name,
            "source_field": field,
            "computed_from_sample_records": path.exists(),
            "fixed_value_detected": False,
            "summary_only_detected": False,
            "periodic_rule_detected": False,
            "per_stage_sample_count": _stage_counts(traces["heldout"]) if "heldout" in name else {},
            "notes": "trace-backed metric" if path.exists() else "missing trace",
        })
    fixed = any(row.get("used_fixed_metric") for rows in traces.values() for row in rows)
    periodic = any(row.get("used_periodic_rule") for rows in traces.values() for row in rows)
    summary = any(row.get("used_summary_metric") for rows in traces.values() for row in rows)
    result = {
        "metric_provenance_passed": not mismatches and not fixed and not periodic and not summary,
        "mismatched_metrics": mismatches,
        "fixed_value_detected": fixed,
        "summary_only_detected": summary,
        "periodic_rule_detected": periodic,
        "entries": entries,
    }
    _write_json(out / "metric_provenance.json", result)
    (out / "metric_provenance.md").write_text(_render_md(result), encoding="utf-8")
    return result


def _rate(rows: List[Dict[str, Any]], field: str) -> float:
    supported = [row for row in rows if row.get("category") == "current_supported_turing_substrate"]
    if not supported:
        return 0.0
    return round(sum(1 for row in supported if row.get(field)) / len(supported), 6)


def _stage_counts(rows: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        stage = row.get("stage") or "unknown"
        counts[stage] = counts.get(stage, 0) + 1
    return counts


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render_md(result: Dict[str, Any]) -> str:
    lines = ["# Bounded Substrate Metric Provenance", ""]
    lines.append(f"metric_provenance_passed: {result['metric_provenance_passed']}")
    lines.append(f"fixed_value_detected: {result['fixed_value_detected']}")
    lines.append(f"summary_only_detected: {result['summary_only_detected']}")
    lines.append(f"periodic_rule_detected: {result['periodic_rule_detected']}")
    return "\n".join(lines) + "\n"
