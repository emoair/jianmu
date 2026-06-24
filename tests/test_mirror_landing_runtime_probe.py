from jianmu.self_learning.darwinforge.mirror_landing_runtime_probe import run_mirror_runtime_probe
from jianmu.self_learning.darwinforge.mirror_landing_schema import MirrorRuntimeProbeConfig


def test_mirror_runtime_probe_records_lane_swap(tmp_path) -> None:
    result = run_mirror_runtime_probe(tmp_path, config=MirrorRuntimeProbeConfig(events=120, minimum_real_compiler_invocations=40, phases=4))
    assert result["lane_swap_executed"] is True
    assert result["mirror_runtime_probe_passed"] is True


def test_mirror_runtime_probe_records_redqueen_adjustment(tmp_path) -> None:
    result = run_mirror_runtime_probe(tmp_path, config=MirrorRuntimeProbeConfig(events=120, minimum_real_compiler_invocations=40, phases=4))
    assert result["redqueen_adjustment_events_from_mirror"] > 0

