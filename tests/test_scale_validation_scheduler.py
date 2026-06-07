from jianmu.self_learning.darwinforge.scale_validation_scheduler import should_run_phase_b


def test_scale_validation_scheduler_requires_phase_a_passed():
    assert should_run_phase_b({"phase_a_passed": True})["phase_b_allowed"] is True


def test_scale_validation_scheduler_blocks_on_phase_a_failure():
    result = should_run_phase_b({"phase_a_passed": False, "phase_a_blocking_issues": ["x"]})
    assert result["phase_b_allowed"] is False
    assert "phase_a_failed" in result["blocking_issues"]

