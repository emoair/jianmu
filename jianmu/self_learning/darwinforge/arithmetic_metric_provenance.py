from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

KEY_METRICS = [
    "supported_candidate_hit_before",
    "supported_candidate_hit_after",
    "supported_correct_output_in_beam_before",
    "supported_correct_output_in_beam_after",
    "top1_supported_correct_before",
    "top1_supported_correct_after",
    "heldout_supported_success_rate",
    "precedence_success_rate",
    "parentheses_success_rate",
    "negative_numbers_success_rate",
    "exact_division_success_rate",
    "unsupported_false_accept_rate",
    "trap_false_accept_rate",
    "future_domain_supported_accept_rate",
    "near_ood_supported_accept_rate",
]


def audit_metric_provenance(records_dir: str | Path, output_dir: str | Path) -> Dict[str, Any]:
    records = Path(records_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    metrics_path = records / "arithmetic_training_metrics.json"
    stage_path = records / "arithmetic_stage_metrics.json"
    metrics = _load_json(metrics_path)
    stage_rows = _load_json(stage_path).get("stages", []) if stage_path.exists() else []
    per_stage_counts = _stage_counts(stage_rows)
    fixed_rule_detected = _fixed_period_rule_detected()
    rows: List[Dict[str, Any]] = []
    for metric in KEY_METRICS:
        value = metrics.get(metric)
        summary_only = True
        fixed_detected = bool(fixed_rule_detected and metric in {
            "supported_candidate_hit_before",
            "supported_candidate_hit_after",
            "supported_correct_output_in_beam_before",
            "supported_correct_output_in_beam_after",
            "top1_supported_correct_before",
            "top1_supported_correct_after",
            "heldout_supported_success_rate",
            "precedence_success_rate",
            "parentheses_success_rate",
            "negative_numbers_success_rate",
            "exact_division_success_rate",
        })
        rows.append({
            "metric_name": metric,
            "source_file": str(metrics_path),
            "source_field": metric,
            "source_value": value,
            "computed_from_sample_records": False,
            "fixed_value_detected": fixed_detected,
            "summary_only_detected": summary_only,
            "per_stage_sample_count": per_stage_counts.get(metric, 0),
            "notes": _notes(metric, fixed_detected, summary_only),
        })
    payload = {
        "metric_provenance_passed": not any(row["fixed_value_detected"] or row["summary_only_detected"] for row in rows),
        "fixed_value_detected": any(row["fixed_value_detected"] for row in rows),
        "summary_only_detected": any(row["summary_only_detected"] for row in rows),
        "fixed_period_rule_detected": fixed_rule_detected,
        "metrics": rows,
    }
    _write_json(out / "metric_provenance.json", payload)
    _write_md(out / "metric_provenance.md", _metric_md(payload))
    return payload


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _stage_counts(stage_rows: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in stage_rows:
        stage = row.get("stage_name")
        count = int(row.get("eval_sample_count", 0))
        if stage == "precedence":
            counts["precedence_success_rate"] = max(counts.get("precedence_success_rate", 0), count)
        elif stage == "parentheses":
            counts["parentheses_success_rate"] = max(counts.get("parentheses_success_rate", 0), count)
        elif stage == "negative_numbers":
            counts["negative_numbers_success_rate"] = max(counts.get("negative_numbers_success_rate", 0), count)
        elif stage == "exact_division":
            counts["exact_division_success_rate"] = max(counts.get("exact_division_success_rate", 0), count)
        elif stage == "mixed_final":
            counts["supported_candidate_hit_before"] = max(counts.get("supported_candidate_hit_before", 0), count)
            counts["supported_candidate_hit_after"] = max(counts.get("supported_candidate_hit_after", 0), count)
            counts["supported_correct_output_in_beam_before"] = max(counts.get("supported_correct_output_in_beam_before", 0), count)
            counts["supported_correct_output_in_beam_after"] = max(counts.get("supported_correct_output_in_beam_after", 0), count)
            counts["top1_supported_correct_before"] = max(counts.get("top1_supported_correct_before", 0), count)
            counts["top1_supported_correct_after"] = max(counts.get("top1_supported_correct_after", 0), count)
    return counts


def _fixed_period_rule_detected() -> bool:
    source = Path("jianmu/self_learning/darwinforge/arithmetic_freebeam_eval.py")
    if not source.exists():
        return False
    text = source.read_text(encoding="utf-8")
    return "base_period = 5" in text and "else 20" in text and "index % base_period" in text


def _notes(metric: str, fixed_detected: bool, summary_only: bool) -> str:
    parts = []
    if summary_only:
        parts.append("v0.9.3 record stores aggregate metric, not per-sample provenance.")
    if fixed_detected:
        parts.append("Metric can be explained by deterministic index-period candidate-hit rule.")
    if metric.endswith("false_accept_rate"):
        parts.append("Boundary metric is aggregate; v0.9.3 does not include per-sample false-accept trace.")
    return " ".join(parts)


def _metric_md(payload: Dict[str, Any]) -> str:
    lines = [
        "# v0.9.3 Arithmetic Metric Provenance Audit",
        "",
        f"- metric_provenance_passed: {payload['metric_provenance_passed']}",
        f"- fixed_value_detected: {payload['fixed_value_detected']}",
        f"- summary_only_detected: {payload['summary_only_detected']}",
        f"- fixed_period_rule_detected: {payload['fixed_period_rule_detected']}",
        "",
        "| metric | fixed | summary_only | notes |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["metrics"]:
        lines.append(f"| {row['metric_name']} | {row['fixed_value_detected']} | {row['summary_only_detected']} | {row['notes']} |")
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_md(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
