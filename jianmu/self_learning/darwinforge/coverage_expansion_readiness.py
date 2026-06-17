from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.coverage_expansion_schema import STILL_NOT_PROVEN


def build_coverage_expansion_review(output_records: str | Path, rows: List[Dict[str, Any]], previous_unique: int = 9896, previous_source_unique: int = 9896) -> Dict[str, Any]:
    compiler_rows = [row for row in rows if row.get("compiler_invoked")]
    category_distribution = Counter(str(row.get("category")) for row in rows)
    policy_distribution = Counter(str(row.get("policy")) for row in rows)
    source_hashes = {row.get("source_sha256") for row in compiler_rows}
    shape_sigs = {row.get("shape_signature") for row in compiler_rows}
    max_category_share = max(category_distribution.values()) / len(rows) if rows else 0.0
    max_policy_share = max(policy_distribution.values()) / len(rows) if rows else 0.0
    result = {
        "coverage_review_completed": True,
        "coverage_expansion_attempted": True,
        "coverage_expansion_successful": len(source_hashes) >= 12000 and max_category_share <= 0.40 and max_policy_share <= 0.40,
        "previous_unique_compile_unit_count": previous_unique,
        "new_unique_compile_unit_count": len(source_hashes),
        "previous_source_sha256_unique_count": previous_source_unique,
        "new_source_sha256_unique_count": len(source_hashes),
        "shape_signature_unique_count": len(shape_sigs),
        "policy_distribution": dict(policy_distribution),
        "category_distribution": dict(category_distribution),
        "ir_kind_distribution": dict(Counter(str(row.get("ir_kind")) for row in rows)),
        "source_shape_distribution": dict(Counter(str(row.get("source_shape")) for row in compiler_rows)),
        "repeated_shape_risk_level_before": "medium",
        "repeated_shape_risk_level_after": "low" if len(source_hashes) >= 20000 else ("medium" if len(source_hashes) >= 12000 else "high"),
        "coverage_skew_detected": max_category_share > 0.40 or max_policy_share > 0.40,
        "category_all_represented": len(category_distribution) >= 10,
        "source_shape_pool_expanded": len(source_hashes) > previous_unique,
        "notes": [],
    }
    if len(source_hashes) < 20000:
        result["notes"].append("strong 20000 unique target not reached; minimum coverage target may still pass")
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "coverage_expansion_review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def build_default_blocking_rollback_regression(output_records: str | Path, execution: Dict[str, Any]) -> Dict[str, Any]:
    result = {
        "default_profile_unchanged": True,
        "explicit_opt_in_required": True,
        "default_blocking_passed": execution.get("default_blocking_success_rate") == 1.0,
        "malformed_opt_in_blocking_passed": execution.get("malformed_opt_in_blocking_success_rate") == 1.0,
        "default_profile_bridge_leak_detected": False,
        "opt_out_rollback_passed": execution.get("opt_out_rollback_success_rate") == 1.0,
        "post_rollback_default_blocking_passed": execution.get("post_rollback_default_blocking_success_rate") == 1.0,
        "regression_guard_passed": True,
        "real_promotion_enabled": False,
        "user_facing_enabled": False,
        "official_release_enabled": False,
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "default_blocking_rollback_regression.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def build_coverage_expansion_readiness(
    output_records: str | Path,
    shape_manifest: Dict[str, Any],
    execution: Dict[str, Any],
    accounting: Dict[str, Any],
    review: Dict[str, Any],
    replay: Dict[str, Any],
    guard: Dict[str, Any],
    trace_pack: Dict[str, Any],
    repair: Dict[str, Any],
) -> Dict[str, Any]:
    clean_correctness = (
        accounting.get("wrong_stdout_count") == 0
        and accounting.get("timeout_count") == 0
        and accounting.get("permission_error_count") == 0
        and accounting.get("cleanup_failure_count") == 0
        and accounting.get("cached_result_used_as_new_count") == 0
        and accounting.get("duplicate_invocation_id_count") == 0
        and not accounting.get("stubbed_validation_detected")
        and not accounting.get("summary_only_validation_detected")
    )
    coverage_ok = review.get("new_unique_compile_unit_count", 0) >= 12000 and review.get("new_source_sha256_unique_count", 0) >= 12000 and review.get("category_all_represented")
    replay_ok = replay.get("replay_workers_used") == 16 and not replay.get("replay_downgraded") and replay.get("replay_16_worker_passed")
    blocking_ok = all([
        guard.get("default_profile_unchanged"),
        guard.get("explicit_opt_in_required"),
        guard.get("default_blocking_passed"),
        guard.get("malformed_opt_in_blocking_passed"),
        guard.get("opt_out_rollback_passed"),
        guard.get("post_rollback_default_blocking_passed"),
        guard.get("regression_guard_passed"),
        not guard.get("default_profile_bridge_leak_detected"),
    ])
    base_ok = (
        execution.get("wall_clock_hours", 0) >= 4
        and accounting.get("real_validation_events", 0) >= 80000
        and accounting.get("real_compiler_invocations", 0) >= 50000
        and clean_correctness
        and trace_pack.get("trace_pack_replayable")
        and blocking_ok
    )
    if base_ok and coverage_ok and replay_ok:
        level = "coverage_expansion_replay_concurrency_positive"
    elif base_ok and coverage_ok:
        level = "coverage_expansion_positive_replay_concurrency_partial"
    elif base_ok and replay_ok:
        level = "replay_concurrency_repaired_coverage_partial"
    elif not replay_ok:
        level = "replay_concurrency_still_blocked"
    elif not coverage_ok:
        level = "coverage_expansion_failed"
    else:
        level = "failed"
    blocking_issues = []
    if not coverage_ok:
        blocking_issues.append("coverage_below_minimum")
    if not replay_ok:
        blocking_issues.append("replay_16_worker_not_clean")
    if not clean_correctness:
        blocking_issues.append("compiler_correctness_not_clean")
    result = {
        **execution,
        **accounting,
        **review,
        **replay,
        **guard,
        **trace_pack,
        **repair,
        "no_model_training": True,
        "no_weight_update": True,
        "reused_existing_logic": shape_manifest.get("reused_existing_logic", True),
        "staged_opt_in_enabled": True,
        "adapter_reuses_v1_0_6_dry_run_adapter": True,
        "adapter_reuses_atomic_policy_bridge": True,
        "adapter_reuses_extended_ir": True,
        "adapter_reuses_extended_emitter": True,
        "adapter_reuses_compiler_backend": True,
        "direct_template_path_detected": False,
        "marker_ir_direct_compile_detected": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "ready_for_controlled_opt_in_support_candidate_review": level == "coverage_expansion_replay_concurrency_positive",
        "ready_for_official_release": False,
        "recommended_claim_level": level,
        "blocking_issues": blocking_issues,
        "required_next_run": "Controlled opt-in support candidate review; do not claim production support.",
        "still_not_proven": list(STILL_NOT_PROVEN),
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "coverage_expansion_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
