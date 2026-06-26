from jianmu.self_learning.darwinforge.opt_active_work_schema import OptActiveWorkConfig, opt_active_work_rate_contract


def test_opt_active_work_schema_defaults() -> None:
    cfg = OptActiveWorkConfig()
    assert cfg.minimum_actual_elapsed_seconds == 2700
    assert cfg.minimum_backend_cl_invocations == 20000
    assert opt_active_work_rate_contract()["opt_active_work_rate_contract_passed"] is True
