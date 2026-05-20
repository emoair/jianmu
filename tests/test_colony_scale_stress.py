from jianmu.self_learning.darwinforge.colony_scale_stress import colony_scale_configs, new_run_id, scales_for_mode, should_skip_scale


def test_colony_scale_config_contains_small_medium_large_full():
    configs = colony_scale_configs()
    assert set(configs) == {"small", "medium", "large", "full"}
    assert configs["large"].cycle_count > configs["medium"].cycle_count


def test_colony_scale_stress_runs_independent_run_ids():
    first = new_run_id("small")
    second = new_run_id("small")
    assert first != second
    assert first.startswith("small-")


def test_full_scale_can_skip_with_reason():
    reason = should_skip_scale("full", allow_full=False)
    assert "full skipped" in reason


def test_scale_metrics_include_runtime_and_sample_counts():
    config = colony_scale_configs()["small"]
    runtime = config.to_runtime_config()
    assert runtime["train_limit"] == 300
    assert runtime["beam_size"] == 24


def test_real_promotion_disabled_for_scale_stress():
    source = open("examples/run_colony_scale_stress_probe.py", encoding="utf-8").read()
    assert "real_promotion_enabled=False" in source


def test_report_contains_chinese_annotations():
    text = open("docs/experiments/COLONY_SCALE_STRESS_PROBE.md", encoding="utf-8").read()
    assert "Colony Scale Stress Probe（根群规模压力探针）" in text
    assert "Bottleneck Diagnosis（瓶颈诊断）" in text


def test_no_expression_oracle_import():
    paths = [
        "jianmu/self_learning/darwinforge/colony_scale_stress.py",
        "jianmu/self_learning/darwinforge/scale_bottleneck_diagnosis.py",
        "examples/run_colony_scale_stress_probe.py",
    ]
    for path in paths:
        assert "expression_oracle" not in open(path, encoding="utf-8").read()


def test_no_external_api_calls():
    source = open("examples/run_colony_scale_stress_probe.py", encoding="utf-8").read()
    assert "requests" not in source
    assert "httpx" not in source
    assert "openai" not in source


def test_free_eval_does_not_read_target_branch_path():
    source = open("jianmu/self_learning/darwinforge/colony_scale_stress.py", encoding="utf-8").read()
    assert "target_branch_path" not in source
