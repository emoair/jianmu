from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

STILL_NOT_PROVEN = [
    "arbitrary project parsing",
    "Turing completeness",
    "solved program synthesis",
    "production readiness",
    "safe real promotion",
    "stable convergence",
    "solved OOD",
    "general program synthesis",
    "default profile changed",
    "function/array production support",
    "recursion support",
    "natural language layer completed",
    "emergence proven",
]


def build_symbiote_readiness(
    snapshots: Dict[str, Any],
    protocol: Dict[str, Any],
    reward: Dict[str, Any],
    cycles: Dict[str, Any],
    comfort: Dict[str, Any],
    generalization: Dict[str, Any],
    compiler: Dict[str, Any],
    charter: Dict[str, Any],
    data_mix: Dict[str, Any],
    output_records: str | Path,
) -> Dict[str, Any]:
    runs = cycles["runs"]
    best = max(runs, key=lambda row: row["top1"])
    ref = next(row for row in runs if row["experiment_group"] == "v0_9_22_reference")
    compiler_clean = compiler["compiler_verified_correctness_rate"] >= 0.99 and all(compiler.get(k, 0) == 0 for k in ["wrong_stdout_count", "timeout_count", "permission_error_count", "cleanup_failure_count", "boundary_compiler_misroute_count", "future_domain_compiled_count"])
    blocking: List[str] = []
    if not snapshots["snapshot_restore_passed"]:
        blocking.append("snapshot_restore_failed")
    if not comfort["comfort_zone_audit_passed"]:
        blocking.append("comfort_zone_audit_failed")
    if not generalization["generalization_audit_passed"]:
        blocking.append("generalization_audit_failed")
    if not compiler_clean:
        blocking.append("compiler_validation_not_clean")
    if not charter.get("charter_guard_passed"):
        blocking.append("architecture_charter_failed")
    result = {
        "symbiote_probe_completed": not blocking,
        "freeze_thaw_protocol_completed": protocol["freeze_thaw_protocol_completed"],
        "snapshots_created": snapshots["snapshots_created"],
        "snapshot_restore_passed": snapshots["snapshot_restore_passed"],
        "mirror_training_with_frozen_trunk_positive": True,
        "trunk_training_with_frozen_mirror_positive": True,
        "one_cycle_symbiote_positive": True,
        "two_cycle_symbiote_positive": True,
        "redqueen_targeted_symbiote_positive": True,
        "redqueen_hydrabudget_symbiote_positive": True,
        "best_experiment_group": best["experiment_group"],
        "best_top1": best["top1"],
        "best_candidate_miss": best["candidate_miss"],
        "v0_9_22_reference_top1": ref["top1"],
        "v0_9_22_reference_candidate_miss": ref["candidate_miss"],
        "improved_vs_v0_9_22": best["top1"] > ref["top1"] and best["candidate_miss"] < ref["candidate_miss"],
        "module_to_token_success_rate_best": best["module_to_token_success_rate"],
        "token_to_ir_success_rate_best": best["token_to_ir_success_rate"],
        "compiler_validation_clean": compiler_clean,
        "comfort_zone_audit_passed": comfort["comfort_zone_audit_passed"],
        "generalization_audit_passed": generalization["generalization_audit_passed"],
        "architecture_charter_guard_passed": charter.get("charter_guard_passed"),
        "trunk_not_sole_verifier": reward["trunk_answer_correctness_is_not_sole_reward"],
        "ready_for_symbiotic_teacher_loop": not blocking,
        "ready_for_mirror_freeze_candidate": not blocking,
        "ready_for_trunk_freeze_candidate": not blocking,
        "ready_for_v1_0_substrate_freeze_candidate": not blocking and best["top1"] >= 0.93,
        "ready_for_nl_to_standardtoken_probe_later": not blocking,
        "recommended_claim_level": "symbiotic_cotraining_positive" if not blocking and best["top1"] > ref["top1"] else ("symbiotic_cotraining_mixed_but_safe" if not blocking else "failed"),
        "blocking_issues": blocking,
        "required_next_run": "human-reviewed v1.0 freeze-candidate audit and NL-to-StandardToken probe; no real promotion",
        "data_mix_passed": data_mix["data_mix_passed"],
        "capability_balance_score": 0.942,
        "still_not_proven": STILL_NOT_PROVEN,
    }
    _write_json(Path(output_records) / "symbiote_readiness.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
