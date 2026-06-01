from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_abstraction_readiness import build_abstraction_readiness
from jianmu.self_learning.darwinforge.mirrorforge_field_ablation import run_field_ablation
from jianmu.self_learning.darwinforge.mirrorforge_nl_bridge_diagnostic import build_nl_bridge_diagnostic
from jianmu.self_learning.darwinforge.mirrorforge_robustness_eval import run_robustness_eval


def test_mirrorforge_abstraction_readiness_claim_levels(tmp_path):
    bundle = run_robustness_eval(tmp_path)
    result = build_abstraction_readiness(
        {"abstraction_variants_generated": True},
        {"ir_similarity_audit_completed": True, "abstraction_risk_score": 0.6},
        {"leakage_audit_passed": True},
        run_field_ablation(tmp_path),
        bundle["robustness"],
        bundle["abstraction_metrics"],
        {
            "compiler_verified_correct_rate": 1.0,
            "wrong_stdout_count": 0,
            "timeout_count": 0,
            "permission_error_count": 0,
            "cleanup_failure_count": 0,
            "boundary_compiler_misroute_count": 0,
            "future_domain_compiled_count": 0,
            "recursion_compiled_count": 0,
            "pointer_compiled_count": 0,
            "io_compiled_count": 0,
        },
        {"charter_guard_passed": True},
        build_nl_bridge_diagnostic(tmp_path),
        tmp_path,
    )
    assert result["recommended_claim_level"] == "mirrorforge_abstraction_robust_teacher_layer"
    assert "Turing completeness" in result["still_not_proven"]
