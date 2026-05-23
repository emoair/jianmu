from __future__ import annotations

from typing import Any, Dict


def reconcile_v0_9_1_claim(
    counters: Dict[str, Any],
    cross_trace: Dict[str, Any],
    baseline_trace: Dict[str, Any],
    ablation_trace: Dict[str, Any],
    runtime_anomaly: Dict[str, Any],
    before_level: str = "large_completed_strong_signal",
) -> Dict[str, Any]:
    blockers = []
    real_xlarge = (
        counters.get("actual_train_iterated_count", 0) > 0
        and counters.get("actual_eval_iterated_count", 0) > 0
        and counters.get("actual_external_ood_iterated_count", 0) > 0
        and counters.get("count_match_passed")
        and cross_trace.get("child_eval_sample_count", 0) > 0
    )
    if not real_xlarge:
        blockers.append("v0.9.1 xlarge real per-sample execution is not verified")
    if runtime_anomaly.get("anomaly_severity") in {"high", "blocking"}:
        blockers.append("runtime anomaly is blocking")
    if not cross_trace.get("cross_process_trace_passed"):
        blockers.append("cross-process execution evidence is insufficient")
    if not baseline_trace.get("baseline_real_execution_verified"):
        blockers.append("baseline real execution is not verified")
    if not ablation_trace.get("ablation_real_execution_verified"):
        blockers.append("ablation real execution is not verified")

    if runtime_anomaly.get("anomaly_severity") == "blocking":
        level = "needs_real_longrun"
    elif not real_xlarge:
        level = "harness_probe_only"
    elif blockers:
        level = "partial_real_workload"
    else:
        level = "real_xlarge_verified"
    return {
        "real_workload_audit_passed": not blockers,
        "v0_9_1_claim_reconciled": True,
        "v0_9_1_claim_level_before": before_level,
        "v0_9_1_claim_level_after": level,
        "recommended_claim_level": level,
        "real_workload_completed": real_xlarge,
        "harness_probe_completed": True,
        "real_xlarge_verified": real_xlarge,
        "baseline_real_execution_verified": baseline_trace.get("baseline_real_execution_verified", False),
        "ablation_real_execution_verified": ablation_trace.get("ablation_real_execution_verified", False),
        "cross_process_real_execution_verified": cross_trace.get("cross_process_trace_passed", False),
        "runtime_anomaly_blocking": runtime_anomaly.get("anomaly_severity") == "blocking",
        "blocking_issues": blockers,
        "required_next_run": "v0.9.1.2 real longrun with mandatory counters" if blockers else "larger real workload reproduction",
    }
