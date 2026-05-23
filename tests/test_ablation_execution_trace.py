from jianmu.self_learning.darwinforge.ablation_execution_trace import audit_ablation_execution, run_real_mini_ablation_trace


def test_ablation_trace_detects_missing_config_change():
    trace = audit_ablation_execution({"results": [{"variant": "no_root_colony", "status": "completed"}]})
    assert trace["ablation_real_execution_verified"] is False
    assert trace["ablations"][0]["config_changed"] is False


def test_real_mini_ablation_trace_changes_config():
    trace = run_real_mini_ablation_trace([{"sample_id": "a"}])
    assert trace["ablation_real_execution_verified"] is True
    assert trace["ablations"][0]["changed_flags"] == ["root_colony_enabled=false"]
