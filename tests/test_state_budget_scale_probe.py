from __future__ import annotations

from jianmu.self_learning.darwinforge.state_budget_scale_probe import run_hundred_million_state_budget_probe
from jianmu.self_learning.darwinforge.turing_frontier_generator import generate_turing_frontier_dataset


def test_state_budget_scale_probe_runs_ordered_profiles(monkeypatch, tmp_path) -> None:
    import jianmu.self_learning.darwinforge.turing_frontier_generator as gen

    monkeypatch.setitem(gen.SCALE_TOTALS, "large", 400)
    root = tmp_path / "frontier"
    generate_turing_frontier_dataset(root, tmp_path / "records", ["large"], 68, 100)
    result = run_hundred_million_state_budget_probe(root, tmp_path / "source", tmp_path / "out", ["baseline_targeted", "state_10M"], 50, 50, run_compiler_validation=False, progress=False, seeds=[74])
    assert result["readiness"]["profiles_attempted"] == ["baseline_targeted", "state_10M"]
    assert result["readiness"]["profiles_completed"] == ["baseline_targeted", "state_10M"]


def test_state_budget_scale_probe_stops_after_unstable_profile(monkeypatch, tmp_path) -> None:
    import jianmu.self_learning.darwinforge.turing_frontier_generator as gen
    import jianmu.self_learning.darwinforge.state_budget_scale_probe as probe

    monkeypatch.setitem(gen.SCALE_TOTALS, "large", 400)
    root = tmp_path / "frontier"
    generate_turing_frontier_dataset(root, tmp_path / "records", ["large"], 68, 100)
    original = probe.allocate_state_budget

    def fake_allocate(profile, guard_row):
        if profile["profile_name"] == "state_10M":
            return {"allocated": False, "skipped_with_reason": "forced_unstable", "actual_state_units_allocated": 0, "peak_memory_bytes": 0, "disk_bytes_written": 0}
        return original(profile, guard_row)

    monkeypatch.setattr(probe, "allocate_state_budget", fake_allocate)
    result = run_hundred_million_state_budget_probe(root, tmp_path / "source", tmp_path / "out", ["baseline_targeted", "state_10M", "state_30M"], 50, 50, run_compiler_validation=False, progress=False, seeds=[74])
    assert result["readiness"]["profiles_skipped"]["state_10M"] == "forced_unstable"
    assert result["readiness"]["profiles_skipped"]["state_30M"] == "previous_profile_unstable"

