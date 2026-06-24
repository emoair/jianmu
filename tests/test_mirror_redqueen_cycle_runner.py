from jianmu.self_learning.darwinforge.mirror_redqueen_8h_schema import MirrorRedQueen8hConfig
from jianmu.self_learning.darwinforge.mirror_redqueen_cycle_runner import run_mirror_redqueen_cycles


def test_mirror_redqueen_cycle_runner_requires_monotonic_time(tmp_path) -> None:
    cfg = MirrorRedQueen8hConfig(planned_wall_clock_hours=0, cycles=1, cycle_min_hours=0, target_events=100, minimum_real_compiler_invocations=20)
    result = run_mirror_redqueen_cycles(tmp_path, {"category_weights": {}}, cfg)
    cycle = result["cycles"][0]
    assert cycle["time"]["minimum_satisfied_by"] == "actual_monotonic_elapsed"
    assert cycle["execution"]["cycle_passed"] is True

