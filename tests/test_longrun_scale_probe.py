import pytest

from jianmu.self_learning.darwinforge.longrun_scale_probe import longrun_scale_configs, should_skip_longrun


def test_longrun_scale_config_contains_large_xlarge_full_longrun():
    assert set(longrun_scale_configs()) == {"large", "xlarge", "full", "longrun"}


def test_longrun_scale_records_partial_or_skip_reason():
    assert "full skipped" in should_skip_longrun("full", bounded_runtime_sec=10)


def test_real_promotion_disabled():
    from examples.run_ood_toxicity_longrun_scale_probe import parse_args
    import sys

    old = sys.argv
    sys.argv = ["x", "--real-promotion", "true"]
    with pytest.raises(SystemExit):
        parse_args()
    sys.argv = old


def test_report_contains_chinese_annotations():
    text = open("docs/experiments/OOD_TOXICITY_LONGRUN_SCALE.md", encoding="utf-8").read()
    assert "OOD Toxicity Taxonomy（分布外毒性分类）" in text
    assert "Long-Run Scale（长时规模）" in text


def test_no_expression_oracle_import():
    paths = [
        "jianmu/self_learning/darwinforge/ood_toxicity_taxonomy.py",
        "jianmu/self_learning/darwinforge/ood_guard_stress.py",
        "jianmu/self_learning/darwinforge/ood_retention_balance.py",
        "jianmu/self_learning/darwinforge/longrun_scale_probe.py",
        "examples/run_ood_toxicity_longrun_scale_probe.py",
    ]
    for path in paths:
        assert "expression_oracle" not in open(path, encoding="utf-8").read()


def test_no_external_api_calls():
    source = open("examples/run_ood_toxicity_longrun_scale_probe.py", encoding="utf-8").read()
    assert "requests" not in source
    assert "httpx" not in source
    assert "openai" not in source


def test_free_eval_does_not_read_target_branch_path():
    source = open("jianmu/self_learning/darwinforge/ood_guard_stress.py", encoding="utf-8").read()
    assert "target_branch_path" not in source
