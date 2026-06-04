from __future__ import annotations

from jianmu.self_learning.darwinforge.project_dataset_builder import build_project_row
from jianmu.self_learning.darwinforge.project_token_audit import audit_project_rows, project_to_token_metrics


def test_project_token_audit_contract_clean() -> None:
    rows = [build_project_row("pilot", i) for i in range(100)]
    audit = audit_project_rows(rows)
    metrics = project_to_token_metrics(rows)
    assert audit["project_token_contains_c_source"] == 0
    assert audit["project_token_contains_raw_target_ir_json"] == 0
    assert metrics["token_schema_valid_rate"] >= 0.98

