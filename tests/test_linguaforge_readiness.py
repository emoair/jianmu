from __future__ import annotations

from jianmu.self_learning.darwinforge.linguaforge_nl_schema import build_linguaforge_row, audit_rows, comfort_zone_audit, evaluate_nl_to_token, evaluate_roundtrip, paraphrase_generalization, readiness


def test_linguaforge_readiness_no_completed_nl_claim() -> None:
    rows = [build_linguaforge_row("pilot", i) for i in range(40)]
    substrate = {"substrate_lock_passed": True}
    dataset = {"dataset_generated": True}
    audit = audit_rows(rows)
    token = evaluate_nl_to_token(rows)
    roundtrip = evaluate_roundtrip(rows)
    compiler = {"backend_claim_safe": True, "compiler_verified_correctness_rate": 1.0}
    ready = readiness(substrate, dataset, audit, token, roundtrip, compiler, paraphrase_generalization(rows), comfort_zone_audit(rows), True)
    assert ready["natural_language_layer_completed"] is False
    assert ready["production_nl_interface"] is False
    assert ready["ready_for_official_release"] is False

