from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def build_v1_0_freeze_readiness(best: Dict[str, Any], audit: Dict[str, Any], compiler: Dict[str, Any], charter: Dict[str, Any], balance: Dict[str, Any], output_records: str | Path | None = None) -> Dict[str, Any]:
    compiler_clean = compiler.get("compiler_verified_correct_rate", 0.0) >= 0.98 and all(compiler.get(k, 0) == 0 for k in ["wrong_stdout_count", "timeout_count", "permission_error_count", "cleanup_failure_count", "boundary_compiler_misroute_count", "future_domain_compiled_count"])
    blocking: List[str] = []
    if best["top1_after"] < 0.90:
        blocking.append("top1_below_0_90")
    if best["candidate_miss_after"] > 0.045:
        blocking.append("candidate_miss_above_0_045")
    if not audit.get("audit_passed"):
        blocking.append("contrastive_full_audit_not_clean")
    if not compiler_clean:
        blocking.append("compiler_validation_not_clean")
    if not charter.get("charter_guard_passed"):
        blocking.append("architecture_charter_not_clean")
    result = {
        "ready_for_v1_0_substrate_freeze_candidate": not blocking,
        "top1_stable_ge_0_90": best["top1_after"] >= 0.90,
        "candidate_miss_stable_le_0_045": best["candidate_miss_after"] <= 0.045,
        "candidate_miss_le_0_040": best["candidate_miss_after"] <= 0.040,
        "contrastive_full_audit_clean": audit.get("audit_passed", False),
        "compiler_validation_clean": compiler_clean,
        "architecture_charter_clean": charter.get("charter_guard_passed", False),
        "data_contract_clean": audit.get("audit_passed", False) and charter.get("charter_guard_passed", False),
        "capability_balance_clean": balance.get("dashboard_passed", balance.get("report_passed", False)),
        "function_array_frontier_observation_positive": best.get("function_array_frontier_observed_top1", 0.0) >= 0.75,
        "default_profile_unchanged": True,
        "real_promotion_disabled": True,
        "freeze_candidate_recommendation": "eligible_for_substrate_freeze_candidate_review" if not blocking else "not_ready",
        "freeze_blocking_issues": blocking,
        "required_before_v1_0": "human architecture review and later dry-run freeze probe" if not blocking else "resolve blocking issues before v1.0 freeze review",
    }
    if output_records is not None:
        Path(output_records).mkdir(parents=True, exist_ok=True)
        (Path(output_records) / "v1_0_freeze_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
