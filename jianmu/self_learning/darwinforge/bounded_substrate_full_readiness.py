from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def assess_bounded_substrate_full_readiness(
    output_records: str | Path,
    signal_audit: Dict[str, Any],
    full_metrics: Dict[str, Any],
    worker_scaling: Dict[str, Any],
) -> Dict[str, Any]:
    out = Path(output_records)
    compiler = _read_json(out / "compiler_validation_metrics.json")
    blockers = []
    if not signal_audit.get("signal_audit_passed"):
        blockers.append("signal audit did not pass")
    if compiler.get("backend_type") != "real_c_compiler":
        blockers.append("compiler validation was not real_c_compiler")
    if compiler.get("compile_failure_count", 0) or compiler.get("runtime_failure_count", 0):
        blockers.append("compiler validation had failures")
    if full_metrics.get("forbidden_field_access_count", 0) != 0:
        blockers.append("forbidden field access detected")
    positive = (
        signal_audit.get("signal_audit_passed", False)
        and full_metrics.get("supported_candidate_hit_after", 0.0) > full_metrics.get("supported_candidate_hit_before", 0.0)
        and full_metrics.get("top1_supported_correct_after", 0.0) > full_metrics.get("top1_supported_correct_before", 0.0)
        and compiler.get("backend_type") == "real_c_compiler"
        and compiler.get("compiler_verified_correct_rate", 0.0) >= 0.98
        and compiler.get("compile_failure_count", 0) == 0
        and compiler.get("runtime_failure_count", 0) == 0
        and compiler.get("boundary_compiler_misroute_count", 0) == 0
        and full_metrics.get("baseline_gap_verified", False)
        and not full_metrics.get("synthetic_summary_detected", False)
        and not full_metrics.get("fixed_metric_detected", False)
        and not full_metrics.get("periodic_rule_detected", False)
    )
    partial = bool(full_metrics.get("modes_partial"))
    if positive and not partial:
        claim = "bounded_substrate_full_positive_signal_verified"
    elif positive:
        claim = "bounded_substrate_full_mixed_signal"
    elif compiler.get("compile_failure_count", 0) or compiler.get("runtime_failure_count", 0):
        claim = "needs_failure_taxonomy"
    elif signal_audit.get("fixed_metric_detected") or signal_audit.get("summary_only_detected") or signal_audit.get("periodic_rule_detected"):
        claim = "signal_not_verified"
    else:
        claim = "failed"
    readiness = {
        "signal_audit_passed": signal_audit.get("signal_audit_passed", False),
        "full_rerun_attempted": True,
        "full_rerun_completed": not partial and bool(full_metrics.get("modes_completed")),
        "full_rerun_partial": partial,
        "full_rerun_partial_reason": "; ".join(full_metrics.get("modes_partial", {}).values()),
        "worker_scaling_completed": worker_scaling.get("worker_scaling_completed", False),
        "best_worker_count_for_bounded_substrate": worker_scaling.get("best_worker_count_for_bounded_substrate"),
        "recommended_default_worker_count": worker_scaling.get("recommended_default_worker_count"),
        "persisted_state_support_level": full_metrics.get("persisted_state_support_level"),
        "cross_process_reload_passed": full_metrics.get("cross_process_reload_passed", False),
        "compiler_validation_completed": compiler.get("real_compiler_invocation_count", 0) > 0,
        "backend_type": compiler.get("backend_type"),
        "compiler_name": compiler.get("compiler_name"),
        "compile_worker_count": compiler.get("compile_worker_count"),
        "real_compiler_invocation_count": compiler.get("real_compiler_invocation_count", 0),
        "compiler_verified_correct_rate": compiler.get("compiler_verified_correct_rate", 0.0),
        "boundary_compiler_misroute_count": compiler.get("boundary_compiler_misroute_count", 0),
        "forbidden_field_access_count": full_metrics.get("forbidden_field_access_count", 0),
        "supported_candidate_hit_before": full_metrics.get("supported_candidate_hit_before", 0.0),
        "supported_candidate_hit_after": full_metrics.get("supported_candidate_hit_after", 0.0),
        "top1_before": full_metrics.get("top1_supported_correct_before", 0.0),
        "top1_after": full_metrics.get("top1_supported_correct_after", 0.0),
        "heldout_supported_success_rate": full_metrics.get("heldout_supported_success_rate", 0.0),
        "baseline_gap_verified": full_metrics.get("baseline_gap_verified", False),
        "synthetic_summary_detected": full_metrics.get("synthetic_summary_detected", False),
        "fixed_metric_detected": full_metrics.get("fixed_metric_detected", False),
        "periodic_rule_detected": full_metrics.get("periodic_rule_detected", False),
        "recommended_claim_level": claim,
        "blocking_issues": blockers,
        "required_next_run": "larger independent bounded substrate rerun; still no Turing-completeness claim",
    }
    _write_json(out / "bounded_substrate_full_readiness.json", readiness)
    return readiness


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
