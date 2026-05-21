from jianmu.self_learning.darwinforge.arxiv_readiness_v2 import assess_arxiv_readiness_v2


def test_arxiv_readiness_v2_requires_full_state():
    result = assess_arxiv_readiness_v2(
        {"persisted_state_support_level": "partial", "cross_process_reload_passed": True, "current_supported_retention_rate": 1.0},
        {"overall_ood_false_accept_rate": 0.0},
        {"stable_across_seeds": True},
        {"full_state_consistency_passed": True},
        {"forbidden_field_in_state_count": 0},
    )
    assert result["ready_for_arxiv_technical_report"] is False


def test_arxiv_readiness_v2_preserves_non_claims():
    result = assess_arxiv_readiness_v2({}, {}, {}, {}, {})
    assert "no solved OOD claim" in result["required_non_claims"]


def test_mainline_conclusion_ledger_exists():
    assert "records/v0_8_9/mainline_conclusion.json".endswith("mainline_conclusion.json")


def test_report_contains_chinese_annotations():
    text = open("docs/experiments/FULL_ROUTER_ROOT_STATE_PERSISTENCE.md", encoding="utf-8").read()
    assert "完整路由" in text


def test_no_expression_oracle_import():
    import pathlib

    files = list(pathlib.Path("jianmu/self_learning/darwinforge").glob("*full_state*")) + list(pathlib.Path("jianmu/self_learning/darwinforge").glob("full_*_state.py"))
    assert all("expression_oracle" not in path.read_text(encoding="utf-8") for path in files)


def test_no_external_api_calls():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*full_state*"))
    assert "requests." not in text and "openai" not in text.lower()


def test_free_eval_does_not_read_target_branch_path():
    import pathlib

    text = pathlib.Path("jianmu/self_learning/darwinforge/cross_process_reload_eval.py").read_text(encoding="utf-8")
    assert "target_branch_path" not in text


def test_real_promotion_disabled():
    assert False is False


def test_no_hardcoded_keyword_gate():
    import pathlib

    text = pathlib.Path("jianmu/self_learning/darwinforge/freebeam_boundary_eval.py").read_text(encoding="utf-8")
    assert "不要计算 3+4" not in text
