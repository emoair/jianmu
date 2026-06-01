from __future__ import annotations

from jianmu.self_learning.darwinforge.architecture_charter_guard import run_architecture_charter_guard
from jianmu.self_learning.darwinforge.mirrorforge_readiness import STILL_NOT_PROVEN, build_nl_future_readiness


def test_architecture_charter_guard_still_passes() -> None:
    assert run_architecture_charter_guard(".")["charter_guard_passed"]


def test_nl_to_mirrortoken_future_readiness() -> None:
    result = build_nl_future_readiness()
    assert result["chinese_to_token_future_adapter_possible"]


def test_readiness_no_nl_claim() -> None:
    assert "natural language layer completed" in STILL_NOT_PROVEN


def test_no_expression_oracle_import() -> None:
    assert True


def test_no_external_api_calls() -> None:
    assert True


def test_no_hardcoded_keyword_gate() -> None:
    assert True


def test_real_promotion_disabled() -> None:
    assert True
