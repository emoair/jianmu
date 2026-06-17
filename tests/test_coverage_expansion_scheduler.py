from jianmu.self_learning.darwinforge.coverage_expansion_scheduler import build_coverage_expansion_schedule, next_coverage_kind


def test_coverage_expansion_scheduler_requires_4h_config():
    targets = {"default_blocking": 1, "arithmetic": 1}
    schedule = build_coverage_expansion_schedule(targets, wall_clock_min_hours=4.0)
    assert schedule["requires_4h_config"] is True
    assert schedule["workers_used"] == 16


def test_coverage_expansion_scheduler_continuation_uses_compiler_kind():
    assert next_coverage_kind({"default_blocking": 1}, {"default_blocking": 1}, 0, True) == "arithmetic"
