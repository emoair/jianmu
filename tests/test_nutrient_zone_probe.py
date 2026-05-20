from pathlib import Path


def test_probe_outputs_nutrient_zone_metrics():
    from examples.run_nutrient_zone_root_colony_probe import _report

    report = _report({"nutrient_zone_count": 2})

    assert "Nutrient Zones（养分区）" in report
    assert "2" in report


def test_report_contains_chinese_annotations():
    from examples.run_nutrient_zone_root_colony_probe import _report

    report = _report({})

    assert "Nutrient-Zone Root Colony（养分区根群）" in report
    assert "Toxic Nutrient（毒性养分）" in report


def test_no_expression_oracle_import():
    for path in Path("jianmu/self_learning/darwinforge").glob("*colony*.py"):
        assert "expression_oracle" not in path.read_text(encoding="utf-8")


def test_no_external_api_calls():
    paths = [
        Path("jianmu/self_learning/darwinforge/nutrient_zone.py"),
        Path("jianmu/self_learning/darwinforge/root_colony.py"),
        Path("examples/run_nutrient_zone_root_colony_probe.py"),
    ]
    for path in paths:
        source = path.read_text(encoding="utf-8")
        assert "requests" not in source
        assert "httpx" not in source
        assert "openai" not in source


def test_free_eval_does_not_read_target_branch_path():
    source = Path("jianmu/self_learning/darwinforge/beam_backtracking.py").read_text(encoding="utf-8")

    assert "target_branch_path" not in source
    assert "target_ir" not in source
    assert "expected_output" not in source
