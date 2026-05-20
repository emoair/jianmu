from pathlib import Path


def test_probe_outputs_before_after_global_beam():
    from examples.run_rootfork_global_assimilation_probe import _report

    report = _report({"global_correct_targetir_in_beam_rate_before": 0.1, "global_correct_targetir_in_beam_rate_after": 0.2})

    assert "Global Beam Before / After（全局束前后）" in report
    assert "0.1" in report
    assert "0.2" in report


def test_report_contains_chinese_annotations():
    from examples.run_rootfork_global_assimilation_probe import _report

    report = _report({})

    assert "RootFork Global Assimilation（根叉全局吸收）" in report
    assert "Root Lifecycle（根生命周期）" in report


def test_no_expression_oracle_import():
    for path in Path("jianmu/self_learning/darwinforge").glob("*assimilation*.py"):
        source = path.read_text(encoding="utf-8")
        assert "expression_oracle" not in source
        assert "parse_controlled_expression" not in source


def test_no_external_api_calls():
    paths = [
        Path("jianmu/self_learning/darwinforge/global_assimilation.py"),
        Path("jianmu/self_learning/darwinforge/root_lifecycle.py"),
        Path("jianmu/self_learning/darwinforge/real_scale_ladder.py"),
        Path("examples/run_rootfork_global_assimilation_probe.py"),
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
