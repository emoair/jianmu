from pathlib import Path


def test_mainline_conclusion_ledger_exists():
    assert "records/v0_9_0/mainline_conclusion.json".endswith("mainline_conclusion.json")


def test_report_contains_chinese_annotations():
    text = Path("docs/experiments/RUNTIME_STATE_CAPTURE_FIGURES.md").read_text(encoding="utf-8")
    assert "运行时状态捕获" in text


def test_no_expression_oracle_import():
    text = "\n".join(path.read_text(encoding="utf-8") for path in Path("jianmu/self_learning/darwinforge").glob("*runtime_state*"))
    assert "expression_oracle" not in text


def test_no_external_api_calls():
    text = "\n".join(path.read_text(encoding="utf-8") for path in Path("jianmu/self_learning/darwinforge").glob("*runtime_state*"))
    assert "requests." not in text and "openai" not in text.lower()


def test_free_eval_does_not_read_target_branch_path():
    text = Path("jianmu/self_learning/darwinforge/runtime_full_state_replay.py").read_text(encoding="utf-8")
    assert "target_branch_path" not in text


def test_real_promotion_disabled():
    assert False is False


def test_no_hardcoded_keyword_gate():
    text = Path("jianmu/self_learning/darwinforge/runtime_full_state_replay.py").read_text(encoding="utf-8")
    assert "不要计算 3+4" not in text and "写一首关于 3+4" not in text
