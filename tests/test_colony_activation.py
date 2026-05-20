from jianmu.self_learning.darwinforge.colony_activation import activate_colonies, summarize_activation
from jianmu.self_learning.darwinforge.local_nutrient_cycle import LocalNutrientCycleConfig, make_test_colony


def test_colony_activation_can_keep_local():
    colony = make_test_colony()
    results = activate_colonies([colony], [{"supported": True}], [], LocalNutrientCycleConfig(cycle_count=1))
    assert results[0].activation_state in {"keep_local", "stable", "nourished"}


def test_colony_activation_does_not_quarantine_all_by_default():
    colonies = [make_test_colony("colony:a", "zone:a"), make_test_colony("colony:b", "zone:b")]
    results = activate_colonies(colonies, [{"supported": True}], [], LocalNutrientCycleConfig(cycle_count=2))
    summary = summarize_activation(results)
    assert summary["quarantined_colony_count"] < len(colonies)


def test_probe_outputs_colony_activation_metrics(tmp_path):
    from examples.run_colony_nutrient_activation_probe import _report

    report = _report(
        {
            "global_correct_targetir_in_beam_rate_before": 0.1,
            "global_correct_targetir_in_beam_rate_after_shadow": 0.1,
            "colony_count": 2,
            "activated_colony_count": 1,
        }
    )
    assert "Colony Nutrient Activation（根群养分激活）" in report
    assert "Shadow Promotion（影子晋升）" in report


def test_report_contains_chinese_annotations():
    text = open("docs/experiments/COLONY_NUTRIENT_ACTIVATION.md", encoding="utf-8").read()
    assert "Toxic Nutrient（毒性养分）" in text
    assert "Keep-Local Colony（保持局部根群）" in text


def test_no_expression_oracle_import():
    paths = [
        "jianmu/self_learning/darwinforge/colony_activation.py",
        "jianmu/self_learning/darwinforge/local_nutrient_cycle.py",
        "jianmu/self_learning/darwinforge/shadow_promotion.py",
        "examples/run_colony_nutrient_activation_probe.py",
    ]
    for path in paths:
        assert "expression_oracle" not in open(path, encoding="utf-8").read()


def test_no_external_api_calls():
    source = open("examples/run_colony_nutrient_activation_probe.py", encoding="utf-8").read()
    assert "requests" not in source
    assert "httpx" not in source
    assert "openai" not in source


def test_free_eval_does_not_read_target_branch_path():
    source = open("jianmu/self_learning/darwinforge/colony_activation.py", encoding="utf-8").read()
    assert "target_branch_path" not in source
