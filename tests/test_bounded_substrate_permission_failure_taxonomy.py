from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_permission_failure_taxonomy import classify_failure_row


def test_permission_failure_taxonomy_classifies_permission_stages() -> None:
    row = {"notes": "validation_exception:PermissionError", "compiler_invoked": False, "latency_ms": 5000}
    assert classify_failure_row(row) == "permission_cleanup_temp_dir"


def test_no_expression_oracle_import() -> None:
    assert "expression_oracle" not in _module_text()


def test_no_external_api_calls() -> None:
    text = _module_text().lower()
    assert "openai" not in text
    assert "requests." not in text


def test_no_hardcoded_keyword_gate() -> None:
    assert "keyword gate" not in _module_text().lower()


def test_real_promotion_disabled() -> None:
    from jianmu.self_learning.darwinforge.turing_substrate_curriculum_schedule import build_turing_substrate_curriculum_schedule

    assert all(not row["real_promotion_allowed"] for row in build_turing_substrate_curriculum_schedule()["stages"])


def _module_text() -> str:
    from pathlib import Path

    return "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in Path("jianmu/self_learning/darwinforge").glob("bounded_substrate_permission*.py"))
