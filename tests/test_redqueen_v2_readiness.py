from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.redqueen_v2_training_probe import run_redqueen_v2_probe


def test_readiness_no_turing_claim(tmp_path) -> None:
    result = run_redqueen_v2_probe("records/v0_9_19", tmp_path / "records", tmp_path / "dataset")
    assert "turing" not in result["readiness"]["recommended_claim_level"].lower()


def test_no_expression_oracle_import() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("*redqueen_v2*.py"):
        text = path.read_text(encoding="utf-8")
        assert "import expression_oracle" not in text
        assert "from expression_oracle" not in text


def test_no_external_api_calls() -> None:
    for path in list(Path("jianmu/self_learning/darwinforge").glob("*redqueen_v2*.py")) + list(Path("jianmu/self_learning/darwinforge").glob("*contrastive_forge*.py")):
        text = path.read_text(encoding="utf-8").lower()
        assert "requests." not in text
        assert "urllib" not in text
        assert "openai" not in text


def test_no_hardcoded_keyword_gate() -> None:
    for path in list(Path("jianmu/self_learning/darwinforge").glob("*redqueen_v2*.py")) + list(Path("jianmu/self_learning/darwinforge").glob("*contrastive_forge*.py")):
        assert "keyword gate" not in path.read_text(encoding="utf-8").lower()


def test_real_promotion_disabled(tmp_path) -> None:
    result = run_redqueen_v2_probe("records/v0_9_19", tmp_path / "records", tmp_path / "dataset")
    assert result["readiness"]["data_contract_clean"] is True
