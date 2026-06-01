from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_v2_freeze_readiness import build_v1_0_freeze_readiness


def test_v1_0_freeze_readiness_requires_clean_gates() -> None:
    best = {"top1_after": 0.91, "candidate_miss_after": 0.04, "function_array_frontier_observed_top1": 0.75}
    audit = {"audit_passed": True}
    compiler = {"compiler_verified_correct_rate": 1.0, "wrong_stdout_count": 0, "timeout_count": 0, "permission_error_count": 0, "cleanup_failure_count": 0, "boundary_compiler_misroute_count": 0, "future_domain_compiled_count": 0}
    charter = {"charter_guard_passed": True}
    balance = {"report_passed": True}
    result = build_v1_0_freeze_readiness(best, audit, compiler, charter, balance)
    assert result["ready_for_v1_0_substrate_freeze_candidate"]
    assert result["real_promotion_disabled"]
