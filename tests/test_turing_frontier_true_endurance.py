from jianmu.self_learning.darwinforge.turing_frontier_true_endurance import run_true_endurance


def test_true_endurance_requires_12h(tmp_path):
    result = run_true_endurance(tmp_path, 12.0, 0.00001, 0.00001, 30, 1, True)
    assert result["endurance_completed"] is False
    assert result["partial"] is True
    assert result["endurance_partial_reason"] == "wall_clock_below_minimum"
    assert result["wall_clock_min_hours_required"] == 12.0


def test_endurance_can_complete_with_small_test_window(tmp_path):
    result = run_true_endurance(tmp_path, 0.00001, 0.001, 0.001, 1, 1, True)
    assert result["endurance_completed"] is True
    assert result["continued_after_sample_target"] is True


def test_continue_after_sample_target(tmp_path):
    result = run_true_endurance(tmp_path, 0.00001, 0.001, 0.001, 1, 1, True)
    assert result["sample_target_completed_early"] is True
    assert result["continued_after_sample_target"] is True
