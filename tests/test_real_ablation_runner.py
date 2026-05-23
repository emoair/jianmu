from jianmu.self_learning.darwinforge.real_ablation_runner import run_real_ablations


def test_real_ablation_runner_config_changed():
    result = run_real_ablations([{"sample_id": "a"}], "real-mini")
    row = result["ablations"][0]
    assert row["config_changed"] is True
    assert row["changed_flags"]
    assert row["metric_from_fixed_summary"] is False
