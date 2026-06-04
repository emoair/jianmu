import importlib
from pathlib import Path

from jianmu.self_learning.darwinforge.algorithm_variant_core import (
    audit_variant_rows,
    build_variant_dataset,
    comfort_zone_metrics,
    heldout_variant_metrics,
    metric_freshness_audit,
    parse_metrics,
    readiness,
    requirement_following_metrics,
    roundtrip_metrics,
    sample_accounting,
    token_metrics,
    variant_family_metrics,
    variant_symbiote_metrics,
)
from jianmu.self_learning.darwinforge.algorithm_variant_generator import build_variant_row
from jianmu.self_learning.darwinforge.projectcartographer_schema import full_compile_validation


def test_comfort_zone_audit():
    rows = [build_variant_row("pilot", i) for i in range(100)]
    assert comfort_zone_metrics(rows)["comfort_zone_audit_passed"] is True


def test_readiness_non_claims_false(tmp_path):
    rows = [build_variant_row("pilot", i) for i in range(100)]
    compiler = {"backend_claim_safe": True}
    ready = readiness(
        {"dataset_generated": True},
        audit_variant_rows(rows),
        metric_freshness_audit(tmp_path, tmp_path),
        sample_accounting(rows),
        parse_metrics(rows),
        token_metrics(rows),
        requirement_following_metrics(rows),
        roundtrip_metrics(rows),
        compiler,
        variant_family_metrics(),
        heldout_variant_metrics(),
        variant_symbiote_metrics(),
        comfort_zone_metrics(rows),
    )
    assert ready["formal_turing_completeness_proven"] is False
    assert ready["production_support"] is False
    assert ready["ready_for_official_release"] is False


def test_no_expression_oracle_import():
    modules = [
        "algorithm_metric_freshness_audit",
        "algorithm_sample_accounting",
        "algorithm_semantic_skeleton",
        "algorithm_requirement_spec",
        "algorithm_variant_generator",
        "algorithm_variant_tokenizer",
        "algorithm_variant_audit",
        "algorithm_variant_roundtrip_eval",
        "algorithm_variant_compiler_validation",
        "algorithm_variant_heldout_taxonomy",
    ]
    for name in modules:
        module = importlib.import_module(f"jianmu.self_learning.darwinforge.{name}")
        assert "expression_oracle" not in str(getattr(module, "__dict__", {}))


def test_no_external_api_calls():
    row = build_variant_row("pilot", 0)
    assert row["provenance"]["external_api_used"] is False
    assert row["provenance"]["llm_generated"] is False


def test_no_hardcoded_keyword_gate():
    source = Path("jianmu/self_learning/darwinforge/algorithm_variant_core.py").read_text(encoding="utf-8")
    assert "keyword rejection" not in source.lower()


def test_real_promotion_disabled():
    row = build_variant_row("pilot", 0)
    assert row["expected_action"] in {"train_current", "review", "isolate_future", "reject"}
