from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional


@dataclass
class MetricRecord:
    run_id: str
    mode: str
    seed: int
    evaluator_name: str
    phase: str
    split_id: str
    train_sample_count: int
    eval_sample_count: int
    ood_sample_count: int
    sample_hashes: Dict[str, str]
    global_correct_targetir_in_beam_rate: Optional[float]
    candidate_space_failure_rate: Optional[float]
    ood_false_accept_rate: Optional[float]
    arithmetic_supported_retention_rate: Optional[float]
    source_record_path: str
    baseline_mode: Optional[str] = None
    baseline_run_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


REQUIRED_PHASES = {"baseline", "before_shadow", "after_shadow", "before_guard", "after_guard"}


def reconcile_metric_records(records: Iterable[MetricRecord | Dict]) -> Dict:
    rows = [row.to_dict() if hasattr(row, "to_dict") else dict(row) for row in records]
    inconsistencies: List[Dict] = []

    for row in rows:
        if not row.get("evaluator_name"):
            inconsistencies.append({"type": "missing_evaluator_name", "run_id": row.get("run_id")})
        if row.get("phase") not in REQUIRED_PHASES:
            inconsistencies.append({"type": "missing_or_unknown_phase", "run_id": row.get("run_id"), "phase": row.get("phase")})
        if row.get("phase") == "after_guard" and row.get("baseline_mode") and row.get("baseline_mode") != row.get("mode"):
            inconsistencies.append({
                "type": "guard_wrong_baseline",
                "run_id": row.get("run_id"),
                "mode": row.get("mode"),
                "baseline_mode": row.get("baseline_mode"),
            })

    grouped: Dict[tuple, List[Dict]] = {}
    for row in rows:
        grouped.setdefault((row.get("run_id"), row.get("mode"), row.get("split_id")), []).append(row)

    for key, group in grouped.items():
        evaluators = {row.get("evaluator_name") for row in group if row.get("evaluator_name")}
        if len(evaluators) > 1:
            inconsistencies.append({"type": "same_field_different_evaluator", "group": key, "evaluators": sorted(evaluators)})
        hashes = {tuple(sorted((row.get("sample_hashes") or {}).items())) for row in group}
        if len(hashes) > 1:
            inconsistencies.append({"type": "split_hash_mismatch", "group": key})
        before = next((row for row in group if row.get("phase") == "before_guard"), None)
        after = next((row for row in group if row.get("phase") == "after_guard"), None)
        if before and after:
            bg = before.get("global_correct_targetir_in_beam_rate")
            ag = after.get("global_correct_targetir_in_beam_rate")
            if bg is not None and ag is not None and abs(float(ag) - float(bg)) > 0.5:
                inconsistencies.append({"type": "guard_global_beam_large_jump", "group": key, "before": bg, "after": ag})
            bo = before.get("ood_false_accept_rate")
            ao = after.get("ood_false_accept_rate")
            if bo is not None and ao is not None and float(ao) > float(bo):
                inconsistencies.append({"type": "before_after_inversion", "group": key, "metric": "ood_false_accept_rate", "before": bo, "after": ao})

    sample_counts = {(row.get("mode"), row.get("train_sample_count"), row.get("eval_sample_count"), row.get("ood_sample_count")) for row in rows}
    corrected_summary = {
        "record_count": len(rows),
        "modes": sorted({row.get("mode") for row in rows if row.get("mode")}),
        "sample_count_tuples": sorted(sample_counts, key=str),
    }
    unresolved = [item for item in inconsistencies if item["type"] in {"guard_wrong_baseline", "split_hash_mismatch", "missing_evaluator_name", "missing_or_unknown_phase"}]
    return {
        "metric_consistency_passed": not inconsistencies,
        "inconsistency_count": len(inconsistencies),
        "inconsistencies": inconsistencies,
        "corrected_summary": corrected_summary,
        "unresolved_issues": unresolved,
    }


def records_from_scale_run(run: Dict, phase: str, evaluator_name: str, source_record_path: str, baseline_mode: Optional[str] = None) -> MetricRecord:
    return MetricRecord(
        run_id=str(run.get("run_id", "")),
        mode=str(run.get("mode") or run.get("scale_label", "")),
        seed=int((run.get("config") or {}).get("seed", run.get("seed", 42))),
        evaluator_name=evaluator_name,
        phase=phase,
        split_id=str(run.get("split_id", "symbol_grounding_v0_7_0")),
        train_sample_count=int(run.get("train_sample_count", 0) or 0),
        eval_sample_count=int(run.get("eval_sample_count", 0) or 0),
        ood_sample_count=int(run.get("ood_sample_count", 0) or 0),
        sample_hashes=dict(run.get("sample_hashes") or {}),
        global_correct_targetir_in_beam_rate=run.get("global_correct_targetir_in_beam_rate"),
        candidate_space_failure_rate=run.get("candidate_space_failure_rate"),
        ood_false_accept_rate=run.get("ood_false_accept_after_shadow", run.get("ood_false_accept_rate")),
        arithmetic_supported_retention_rate=run.get("arithmetic_supported_retention_rate"),
        source_record_path=source_record_path,
        baseline_mode=baseline_mode or str(run.get("mode") or run.get("scale_label", "")),
        baseline_run_id=run.get("run_id"),
    )
