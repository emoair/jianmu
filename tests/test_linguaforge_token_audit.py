from __future__ import annotations

from jianmu.self_learning.darwinforge.linguaforge_nl_schema import build_linguaforge_row
from jianmu.self_learning.darwinforge.linguaforge_token_audit import audit_rows, evaluate_nl_to_token


def test_linguaforge_token_audit_clean_contract() -> None:
    rows = [build_linguaforge_row("pilot", i) for i in range(30)]
    audit = audit_rows(rows)
    metrics = evaluate_nl_to_token(rows)
    assert audit["nl_direct_c_generation_count"] == 0
    assert audit["token_contains_raw_target_ir_json"] == 0
    assert metrics["token_schema_audit_passed"] is True

