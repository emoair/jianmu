from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_training_readiness import assess_bounded_substrate_readiness


def test_bounded_substrate_readiness_no_turing_complete_claim() -> None:
    result = assess_bounded_substrate_readiness({"mandatory_counter_guard_passed": False})
    text = str(result).lower()
    assert "turing_complete" not in text
    assert "production_ready" not in text


def test_no_expression_oracle_import() -> None:
    from pathlib import Path

    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in Path("jianmu/self_learning/darwinforge").glob("bounded_substrate_*.py"))
    assert "expression_oracle" not in text


def test_no_external_api_calls() -> None:
    from pathlib import Path

    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore").lower() for path in Path("jianmu/self_learning/darwinforge").glob("bounded_substrate_*.py"))
    assert "openai" not in text
    assert "requests." not in text


def test_no_hardcoded_keyword_gate() -> None:
    from pathlib import Path

    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore").lower() for path in Path("jianmu/self_learning/darwinforge").glob("bounded_substrate_*.py"))
    assert "keyword gate" not in text


def test_real_promotion_disabled() -> None:
    from jianmu.self_learning.darwinforge.turing_substrate_curriculum_schedule import build_turing_substrate_curriculum_schedule

    assert all(not row["real_promotion_allowed"] for row in build_turing_substrate_curriculum_schedule()["stages"])
