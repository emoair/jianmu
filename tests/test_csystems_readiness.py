import importlib
from pathlib import Path

from jianmu.self_learning.darwinforge.csystems_frontier_core import (
    audit_dataset_rows,
    build_csystems_row,
    comfort_zone_audit,
    family_metrics,
    fileio_sandbox_audit,
    heldout_metrics,
    memory_contract_audit,
    multifile_build_validation,
    parse_metrics,
    readiness,
    roundtrip_metrics,
    token_metrics,
)


def test_readiness_requires_full_completed_for_positive(tmp_path):
    rows = [build_csystems_row(i) for i in range(120)]
    ready = readiness(
        {"dataset_generated": True, "full_scale_attempted": True, "full_scale_completed": False, "full_runtime_hours": 0.1},
        audit_dataset_rows(rows),
        parse_metrics(rows),
        token_metrics(rows),
        roundtrip_metrics(rows),
        memory_contract_audit(rows),
        fileio_sandbox_audit(rows),
        multifile_build_validation(rows, tmp_path, target=1),
        {"backend_claim_safe": True, "full_compile_50k_clean": True, "real_compiler_invocation_count": 50_000},
        heldout_metrics(),
        family_metrics(),
        comfort_zone_audit(),
    )
    assert ready["recommended_claim_level"] == "full_scale_not_completed"
    assert "full_scale_not_completed" in ready["blocking_issues"]


def test_readiness_non_claims_false(tmp_path):
    rows = [build_csystems_row(i) for i in range(120)]
    ready = readiness(
        {"dataset_generated": True, "full_scale_attempted": True, "full_scale_completed": True, "full_runtime_hours": 0.1},
        audit_dataset_rows(rows),
        parse_metrics(rows),
        token_metrics(rows),
        roundtrip_metrics(rows),
        memory_contract_audit(rows),
        fileio_sandbox_audit(rows),
        multifile_build_validation(rows, tmp_path, target=1),
        {"backend_claim_safe": True, "full_compile_50k_clean": True, "real_compiler_invocation_count": 50_000},
        heldout_metrics(),
        family_metrics(),
        comfort_zone_audit(),
    )
    assert ready["arbitrary_project_parsing_completed"] is False
    assert ready["memory_safety_solved"] is False
    assert ready["production_support"] is False


def test_csystems_failure_taxonomy():
    from jianmu.self_learning.darwinforge.csystems_failure_analysis import failure_taxonomy

    assert "link_failure" in failure_taxonomy()["failure_category_distribution"]


def test_no_expression_oracle_import():
    module = importlib.import_module("jianmu.self_learning.darwinforge.csystems_frontier_core")
    assert "expression_oracle" not in str(module.__dict__)


def test_no_external_api_calls():
    row = build_csystems_row(0)
    assert row["provenance"]["external_api_used"] is False
    assert row["provenance"]["llm_generated"] is False


def test_no_hardcoded_keyword_gate():
    text = Path("jianmu/self_learning/darwinforge/csystems_frontier_core.py").read_text(encoding="utf-8")
    assert "keyword rejection" not in text.lower()


def test_real_promotion_disabled():
    row = build_csystems_row(0)
    assert row["expected_action"] in {"train_current", "review", "reject"}
