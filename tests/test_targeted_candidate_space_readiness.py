from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.targeted_candidate_space_profile import targeted_candidate_space_profile
from jianmu.self_learning.darwinforge.targeted_candidate_space_readiness import build_targeted_readiness


def test_readiness_no_turing_complete_claim(tmp_path) -> None:
    profile = targeted_candidate_space_profile()
    rerun = {
        "targeted_rerun_partial": False,
        "partial_reason": "",
        "fresh_ratio": 1.0,
        "candidate_miss_rate_baseline_reference": 0.6024,
        "candidate_miss_rate_targeted": 0.23,
        "candidate_miss_reduction": 0.37,
        "correct_output_in_beam_targeted": 0.74,
        "top1_targeted": 0.66,
        "top1_delta": 0.28,
        "boundary_false_accept_rate": 0.0,
        "future_domain_supported_accept_rate": 0.0,
    }
    compiler = {"compiler_validation_completed": True, "compiler_verified_correct_rate": 1.0, "boundary_compiler_misroute_count": 0, "future_domain_compiled_count": 0}
    integrity = {"forbidden_field_access_count": 0}
    result = build_targeted_readiness(tmp_path, profile, rerun, compiler, integrity, True)
    assert result["recommended_claim_level"] == "targeted_candidate_space_expansion_reproduced"
    text = (tmp_path / "targeted_candidate_space_readiness.json").read_text(encoding="utf-8").lower()
    assert "turing complete" not in text


def test_integrity_check_no_forbidden_fields(tmp_path) -> None:
    path = tmp_path / "integrity_check.json"
    path.write_text(json.dumps({"forbidden_field_access_count": 0, "profile_is_architecture_change": False}), encoding="utf-8")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["forbidden_field_access_count"] == 0
    assert data["profile_is_architecture_change"] is False


def test_no_expression_oracle_import() -> None:
    text = Path("jianmu/self_learning/darwinforge/targeted_candidate_space_rerun.py").read_text(encoding="utf-8")
    assert "expression_oracle" not in text


def test_no_external_api_calls() -> None:
    text = Path("jianmu/self_learning/darwinforge/targeted_candidate_space_rerun.py").read_text(encoding="utf-8").lower()
    assert "openai" not in text
    assert "requests." not in text


def test_no_hardcoded_keyword_gate() -> None:
    text = Path("jianmu/self_learning/darwinforge/targeted_candidate_space_eval.py").read_text(encoding="utf-8").lower()
    assert "keyword gate" not in text


def test_real_promotion_disabled() -> None:
    text = Path("docs/experiments/TARGETED_CANDIDATE_SPACE_EXPANSION_RERUN.md").read_text(encoding="utf-8").lower()
    assert "safe real promotion" in text

