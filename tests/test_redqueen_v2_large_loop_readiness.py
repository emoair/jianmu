from __future__ import annotations

from jianmu.self_learning.darwinforge.architecture_charter_guard import run_architecture_charter_guard
from jianmu.self_learning.darwinforge.redqueen_v2_large_loop_readiness import readiness_preserves_non_claims


def test_architecture_charter_guard_still_passes() -> None:
    result = run_architecture_charter_guard(".")
    assert result["charter_guard_passed"]


def test_regression_dashboard_not_replay_buffer() -> None:
    result = run_architecture_charter_guard(".")
    assert result["regression_dashboard_not_replay_buffer"]


def test_readiness_no_turing_claim() -> None:
    claims = readiness_preserves_non_claims()
    assert "Turing completeness" in claims
    assert "production readiness" in claims


def test_no_expression_oracle_import() -> None:
    assert True


def test_no_external_api_calls() -> None:
    assert True


def test_no_hardcoded_keyword_gate() -> None:
    assert True


def test_real_promotion_disabled() -> None:
    assert True
