from __future__ import annotations

from jianmu.self_learning.darwinforge.clean_validation_readiness import assess_clean_validation_readiness


def test_clean_validation_readiness_no_turing_complete_claim(tmp_path) -> None:
    result = assess_clean_validation_readiness(
        tmp_path,
        {"preflight_passed": True, "cl_bv_test_passed": True},
        {"primary": {"executed": True, "completed": True, "real_compiler_invocation_count": 1, "permission_error_count": 0, "compiler_verified_correct_rate": 1.0, "boundary_compiler_misroute_count": 0, "backend_claim_safe": True}, "fallback": {"executed": False}},
    )
    assert result["recommended_claim_level"] == "independent_compiler_validation_restored"
    assert "Turing completeness" not in str(result)


def test_no_expression_oracle_import() -> None:
    assert "expression_oracle" not in _module_text()


def test_no_external_api_calls() -> None:
    text = _module_text().lower()
    assert "openai" not in text
    assert "requests." not in text


def test_no_hardcoded_keyword_gate() -> None:
    assert "keyword gate" not in _module_text().lower()


def test_real_promotion_disabled() -> None:
    from jianmu.self_learning.darwinforge.turing_substrate_curriculum_schedule import build_turing_substrate_curriculum_schedule

    assert all(not row["real_promotion_allowed"] for row in build_turing_substrate_curriculum_schedule()["stages"])


def _module_text() -> str:
    from pathlib import Path

    names = ["clean_msvc_preflight.py", "bounded_substrate_clean_independent_validation.py", "clean_validation_readiness.py"]
    return "\n".join((Path("jianmu/self_learning/darwinforge") / name).read_text(encoding="utf-8", errors="ignore") for name in names)
