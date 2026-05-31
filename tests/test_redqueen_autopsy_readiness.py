from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.redqueen_autopsy import run_redqueen_autopsy


def test_readiness_no_capability_claim(tmp_path: Path) -> None:
    result = run_redqueen_autopsy("records/v0_9_17", "records/v0_9_18", "records/v0_9_18_2", "datasets/v0_9_17_redqueen_curriculum", tmp_path)
    readiness = result["redqueen_autopsy_readiness"]
    assert readiness["ready_for_redqueen_v2_bandit_scheduler"] is True
    assert "capability_improved" not in readiness["recommended_claim_level"]


def test_no_expression_oracle_import() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("redqueen_*.py"):
        text = path.read_text(encoding="utf-8")
        assert "import expression_oracle" not in text
        assert "from expression_oracle" not in text


def test_no_external_api_calls() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("redqueen_*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "requests." not in text
        assert "urllib" not in text
        assert "openai" not in text


def test_no_hardcoded_keyword_gate() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("redqueen_*.py"):
        assert "keyword gate" not in path.read_text(encoding="utf-8").lower()


def test_real_promotion_disabled(tmp_path: Path) -> None:
    result = run_redqueen_autopsy("records/v0_9_17", "records/v0_9_18", "records/v0_9_18_2", "datasets/v0_9_17_redqueen_curriculum", tmp_path)
    assert result["integrity_check"]["real_promotion_enabled"] is False
