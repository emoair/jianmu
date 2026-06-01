from jianmu.self_learning.darwinforge.turing_frontier_longhaul import longhaul_audit


def test_longhaul_wall_clock_minimum_enforced(tmp_path):
    result = longhaul_audit(tmp_path, start=0.0, wall_clock_min_hours=6.0, rolling_window_minutes=30)
    assert result["wall_clock_hours"] > 6
    assert result["endurance_completed"] is True


def test_endurance_partial_if_below_6h(tmp_path):
    import time

    result = longhaul_audit(tmp_path, start=time.time(), wall_clock_min_hours=6.0, rolling_window_minutes=30)
    assert result["endurance_completed"] is False
    assert result["endurance_partial"] is True
    assert result["endurance_partial_reason"] == "wall_clock_below_minimum"
