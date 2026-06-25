from jianmu.self_learning.darwinforge.opt_live_display_schema import OptTrue8hConfig
from jianmu.self_learning.darwinforge.true8h_backend_validation_runner import run_true8h_backend_validation


def test_true8h_backend_validation_runner_requires_opt_gate(tmp_path) -> None:
    result = run_true8h_backend_validation(tmp_path, tmp_path / "artifacts", OptTrue8hConfig(wall_clock_min_hours=0, minimum_backend_cl_invocations=0), opt_gate_passed=False)
    assert result["true8h_validation_started"] is False
    assert result["true8h_backend_validation_passed"] is False
