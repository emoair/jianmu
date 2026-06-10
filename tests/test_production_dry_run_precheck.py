from jianmu.self_learning.darwinforge.production_dry_run_precheck import write_production_dry_run_precheck


def test_production_dry_run_precheck_does_not_execute_production(tmp_path):
    result = write_production_dry_run_precheck(tmp_path, True)
    assert result["production_dry_run_executed"] is False
    assert result["ready_for_production_dry_run_candidate"] is True
    assert result["production_ready"] is False

