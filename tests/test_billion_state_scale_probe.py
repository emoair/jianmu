from __future__ import annotations

from jianmu.self_learning.darwinforge.billion_state_scale_probe import run_billion_state_budget_upper_frontier_probe
from jianmu.self_learning.darwinforge.turing_frontier_generator import generate_turing_frontier_dataset


def test_billion_state_scale_probe_runs_ordered_profiles(monkeypatch, tmp_path) -> None:
    import jianmu.self_learning.darwinforge.turing_frontier_generator as gen

    monkeypatch.setitem(gen.SCALE_TOTALS, "large", 400)
    root = tmp_path / "frontier"
    generate_turing_frontier_dataset(root, tmp_path / "records", ["large"], 68, 100)
    result = run_billion_state_budget_upper_frontier_probe(root, tmp_path / "source", tmp_path / "baseline", tmp_path / "out", ["state_100M_reference", "state_300M"], 50, 50, run_compiler_validation=False, progress=False, seeds=[77])
    assert result["readiness"]["profiles_attempted"] == ["state_100M_reference", "state_300M"]
    assert result["readiness"]["profiles_completed"] == ["state_100M_reference", "state_300M"]


def test_billion_state_scale_probe_stops_after_unstable_profile(monkeypatch, tmp_path) -> None:
    import jianmu.self_learning.darwinforge.billion_state_scale_probe as probe
    import jianmu.self_learning.darwinforge.turing_frontier_generator as gen

    monkeypatch.setitem(gen.SCALE_TOTALS, "large", 400)
    root = tmp_path / "frontier"
    generate_turing_frontier_dataset(root, tmp_path / "records", ["large"], 68, 100)
    original = probe.allocate_billion_state_budget

    def fake_allocate(profile, guard):
        if profile["profile_name"] == "state_300M":
            return {"allocated": False, "skipped_with_reason": "forced_unstable", "actual_state_units_allocated": 0, "materialization_level": "", "peak_memory_bytes": 0, "disk_bytes_written": 0}
        return original(profile, guard)

    monkeypatch.setattr(probe, "allocate_billion_state_budget", fake_allocate)
    result = run_billion_state_budget_upper_frontier_probe(root, tmp_path / "source", tmp_path / "baseline", tmp_path / "out", ["state_100M_reference", "state_300M", "state_600M"], 50, 50, run_compiler_validation=False, progress=False, seeds=[77])
    assert result["readiness"]["profiles_skipped"]["state_300M"] == "forced_unstable"
    assert result["readiness"]["profiles_skipped"]["state_600M"] == "previous_profile_unstable"

