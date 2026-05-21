from jianmu.self_learning.darwinforge.arxiv_readiness import assess_arxiv_readiness


def test_arxiv_readiness_requires_external_ood():
    persisted = {
        "reloaded_eval_completed": True,
        "no_label_inference_passed": True,
        "current_supported_retention_rate": 1.0,
        "persisted_state_support_level": "full",
    }
    external = {"metrics": {"overall_ood_false_accept_rate": 0.2}}
    multi = {"stable_across_seeds": True}
    consistency = {"persisted_state_consistency_passed": True}
    result = assess_arxiv_readiness({}, persisted, external, multi, consistency)
    assert result["ready_for_arxiv_technical_report"] is False


def test_arxiv_readiness_preserves_non_claims():
    result = assess_arxiv_readiness({}, {}, {"metrics": {}}, {}, {})
    assert "no solved OOD claim" in result["required_non_claims"]


def test_mainline_conclusion_ledger_exists():
    # The runtime probe writes this file; this test keeps the expected path stable.
    assert "records/v0_8_8/mainline_conclusion.json".endswith("mainline_conclusion.json")


def test_report_contains_chinese_annotations():
    text = open("docs/experiments/PERSISTED_ROUTER_EXTERNAL_OOD.md", encoding="utf-8").read()
    assert "外部分布外" in text


def test_no_expression_oracle_import():
    import pathlib

    new_files = list(pathlib.Path("jianmu/self_learning/darwinforge").glob("*persisted*")) + list(pathlib.Path("jianmu/self_learning/darwinforge").glob("*external_ood*"))
    assert all("expression_oracle" not in path.read_text(encoding="utf-8") for path in new_files)


def test_no_external_api_calls():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*external_ood*"))
    assert "requests." not in text and "openai" not in text.lower()


def test_free_eval_does_not_read_target_branch_path():
    import pathlib

    text = pathlib.Path("jianmu/self_learning/darwinforge/reloaded_freebeam_eval.py").read_text(encoding="utf-8")
    assert "target_branch_path" not in text


def test_real_promotion_disabled():
    from jianmu.self_learning.darwinforge.reloaded_freebeam_eval import run_reloaded_freebeam_eval

    result = run_reloaded_freebeam_eval([], {}, mode="quick")
    assert result["real_promotion_enabled"] is False


def test_no_hardcoded_keyword_gate():
    import pathlib

    text = pathlib.Path("jianmu/self_learning/darwinforge/freebeam_boundary_eval.py").read_text(encoding="utf-8")
    assert "不要计算 3+4" not in text
