from jianmu.self_learning.darwinforge.real_baseline_runner import run_real_baselines


def test_real_baseline_runner_sample_metrics():
    result = run_real_baselines([{"sample_id": "a"}, {"sample_id": "b"}], "real-mini")
    assert result["baseline_real_execution_verified"] is True
    assert result["baselines"][0]["metric_computed_from_samples"] is True
    assert result["baselines"][0]["used_forbidden_fields"] is False
