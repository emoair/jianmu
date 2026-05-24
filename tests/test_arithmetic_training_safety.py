from pathlib import Path


def test_no_expression_oracle_import():
    files = Path("jianmu/self_learning/darwinforge").glob("arithmetic_*.py")
    text = "\n".join(path.read_text(encoding="utf-8") for path in files)
    assert "import expression_oracle" not in text
    assert "from expression_oracle" not in text


def test_no_external_api_calls():
    files = Path("jianmu/self_learning/darwinforge").glob("arithmetic_*.py")
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in files)
    forbidden = ["openai", "anthropic", "claude", "gemini", "dashscope", "kimi"]
    assert not any(token in text for token in forbidden)


def test_no_hardcoded_keyword_gate():
    files = Path("jianmu/self_learning/darwinforge").glob("arithmetic_*.py")
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in files)
    assert "keyword gate" not in text
    assert "if \"sqrt\"" not in text
    assert "if 'sqrt'" not in text


def test_real_promotion_disabled():
    text = Path("docs/experiments/ARITHMETIC_TRAINING_PROBE.md").read_text(encoding="utf-8")
    assert "safe real promotion" in text
