from __future__ import annotations

from jianmu.self_learning.darwinforge.project_substrate_readiness import readiness


def test_project_substrate_readiness_no_forbidden_claims() -> None:
    dataset = {"dataset_generated": True}
    audit = {"audit_passed": True, "project_token_contains_c_source": 0, "project_token_contains_raw_target_ir_json": 0, "token_contains_expected_output": 0, "unsupported_has_targetir": 0, "unsupported_has_expected_output": 0, "future_domain_in_train_current": 0, "arbitrary_project_claim_count": 0, "production_support_claim_count": 0}
    parse = {"project_parse_success_rate": 1.0}
    token = {"project_to_token_overall_success_rate": 1.0, "token_schema_valid_rate": 1.0}
    roundtrip = {"token_to_ir_success_rate": 1.0}
    compiler = {"backend_claim_safe": True}
    sym = {"project_symbiote_positive": True, "function_array_success_rate": 0.918, "counter_machine_project_witness_success_rate": 0.981, "heldout_project_success_rate": 0.914}
    comfort = {"comfort_zone_audit_passed": True}
    ready = readiness(dataset, audit, parse, token, roundtrip, {}, compiler, sym, comfort)
    assert ready["arbitrary_project_parsing_completed"] is False
    assert ready["formal_turing_completeness_proven"] is False
    assert ready["natural_language_layer_completed"] is False
    assert ready["ready_for_official_release"] is False

