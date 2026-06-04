from __future__ import annotations

from jianmu.self_learning.darwinforge.algorithm_token_audit import audit_algorithm_rows, token_metrics
from jianmu.self_learning.darwinforge.forgecorpus_algorithm_schema import build_algorithm_row


def test_algorithm_token_audit_no_leakage() -> None:
    rows = [build_algorithm_row("pilot", i) for i in range(100)]
    audit = audit_algorithm_rows(rows)
    metrics = token_metrics(rows)
    assert audit["token_contains_c_source_count"] == 0
    assert audit["token_contains_raw_target_ir_json_count"] == 0
    assert metrics["token_schema_valid_rate"] >= 0.98

