from __future__ import annotations

from jianmu.self_learning.darwinforge.ironjudge_level_semantics import detect_level_accounting_mode, reconcile_effective_invocations


def test_ironjudge_level_semantics_cumulative() -> None:
    scaleup = {"levels": [{"level_name": "gate_5k", "completed_invocations": 5000, "previous_invocations_used": 2848}, {"level_name": "main_20k", "completed_invocations": 16440, "previous_invocations_used": 5000}, {"level_name": "extended_50k", "completed_invocations": 27800, "previous_invocations_used": 16440}]}
    assert detect_level_accounting_mode(scaleup)["level_accounting_mode_detected"] == "cumulative"
    effective = reconcile_effective_invocations(scaleup, {"total_accounted_invocation_count": 27800}, "cumulative")
    assert effective["main_20k_effective_invocations"] == 27800


def test_ironjudge_level_semantics_independent() -> None:
    scaleup = {"levels": [{"level_name": "gate_5k", "completed_invocations": 5000, "previous_invocations_used": 0}, {"level_name": "main_20k", "completed_invocations": 16440, "previous_invocations_used": 0}, {"level_name": "extended_50k", "completed_invocations": 27800, "previous_invocations_used": 0}]}
    assert detect_level_accounting_mode(scaleup)["level_accounting_mode_detected"] == "independent"
    effective = reconcile_effective_invocations(scaleup, {"total_accounted_invocation_count": 27800}, "independent")
    assert effective["main_20k_effective_invocations"] == 16440
