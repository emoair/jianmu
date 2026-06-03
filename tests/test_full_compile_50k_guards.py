from pathlib import Path


FILES = [
    Path("jianmu/self_learning/darwinforge/full_compile_50k_continuation_core.py"),
    Path("jianmu/self_learning/darwinforge/full_compile_50k_accounting.py"),
    Path("jianmu/self_learning/darwinforge/full_compile_50k_continuation_runner.py"),
]


def test_no_expression_oracle_import() -> None:
    for path in FILES:
        assert "expression_oracle" not in path.read_text(encoding="utf-8")


def test_no_external_api_calls() -> None:
    forbidden = ["requests.", "urllib.request", "httpx.", "openai", "anthropic"]
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        assert not any(item in text for item in forbidden)


def test_no_hardcoded_keyword_gate() -> None:
    text = Path("jianmu/self_learning/darwinforge/full_compile_50k_continuation_core.py").read_text(encoding="utf-8").lower()
    assert "keyword rejection" not in text
    assert "blacklist" not in text


def test_real_promotion_disabled() -> None:
    text = Path("jianmu/self_learning/darwinforge/full_compile_50k_continuation_core.py").read_text(encoding="utf-8")
    assert '"ready_for_v1_0_release": False' in text
    assert "default_profile_unchanged" in text
