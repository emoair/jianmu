from pathlib import Path


NEW_FILES = [
    Path("jianmu/self_learning/darwinforge/frontier_review_proof_readiness_rc_prep.py"),
    Path("jianmu/self_learning/darwinforge/frontier_review_evidence_chain.py"),
    Path("jianmu/self_learning/darwinforge/frontier_review_function_array.py"),
    Path("jianmu/self_learning/darwinforge/frontier_review_turing.py"),
]


def test_no_formal_turing_claim_unless_proof_passed() -> None:
    text = Path("jianmu/self_learning/darwinforge/frontier_review_proof_readiness_rc_prep.py").read_text(encoding="utf-8")
    assert '"formal_turing_completeness_proven": False' in text
    assert "finite_validation_is_not_formal_proof" in text


def test_no_expression_oracle_import() -> None:
    for path in NEW_FILES:
        assert "expression_oracle" not in path.read_text(encoding="utf-8")


def test_no_external_api_calls() -> None:
    forbidden = ["requests.", "urllib.request", "openai", "anthropic", "httpx."]
    for path in NEW_FILES:
        text = path.read_text(encoding="utf-8")
        assert not any(item in text for item in forbidden)


def test_no_hardcoded_keyword_gate() -> None:
    text = Path("jianmu/self_learning/darwinforge/frontier_review_proof_readiness_rc_prep.py").read_text(encoding="utf-8").lower()
    assert "keyword rejection" not in text
    assert "blacklist" not in text


def test_real_promotion_disabled() -> None:
    text = Path("jianmu/self_learning/darwinforge/frontier_review_proof_readiness_rc_prep.py").read_text(encoding="utf-8")
    assert "ready_for_v1_0_release\": False" in text
    assert "profile_is_default_runtime" not in text
