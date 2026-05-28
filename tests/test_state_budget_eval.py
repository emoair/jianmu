from __future__ import annotations

from jianmu.self_learning.darwinforge.state_budget_allocator import allocate_state_budget
from jianmu.self_learning.darwinforge.state_budget_eval import analyze_scaling_law, evaluate_state_budget_profile
from jianmu.self_learning.darwinforge.state_budget_memory_guard import run_state_budget_memory_guard
from jianmu.self_learning.darwinforge.state_budget_profile import build_state_budget_profiles


def test_state_budget_eval_detects_diminishing_returns(tmp_path) -> None:
    profiles = build_state_budget_profiles(["baseline_targeted", "state_10M", "state_30M", "state_100M"])
    guard = {row["profile_name"]: row for row in run_state_budget_memory_guard(tmp_path, profiles)["profiles"]}
    supported = [{"id": f"s{i}", "stage": "bounded_for_loop", "category": "bounded_control_hard_supported"} for i in range(100)]
    rows = [evaluate_state_budget_profile(profile, supported, [], allocate_state_budget(profile, guard[profile["profile_name"]])) for profile in profiles]
    result = analyze_scaling_law(tmp_path, rows)
    assert result["diminishing_returns_detected"] is True


def test_state_budget_eval_does_not_claim_emergence_proven(tmp_path) -> None:
    result = analyze_scaling_law(tmp_path, [])
    assert result["emergence_proven"] is False

