from jianmu.self_learning.darwinforge.opt_live_display_schema import OptTrue8hConfig, opt_live_display_contract


def test_opt_live_display_schema() -> None:
    cfg = OptTrue8hConfig(progress_interval_seconds=10, heartbeat_interval_seconds=300)
    contract = opt_live_display_contract(cfg.progress_interval_seconds, cfg.heartbeat_interval_seconds)
    assert contract["opt_live_display_contract_passed"] is True
    assert contract["progress_lines_include_backend_counts"] is True
