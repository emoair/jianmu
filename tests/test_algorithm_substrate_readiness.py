from __future__ import annotations

from jianmu.self_learning.darwinforge.forgecorpus_algorithm_schema import readiness


def test_readiness_non_claims_false() -> None:
    dataset = {"dataset_generated": True}
    audit = {"audit_passed": True, "token_contains_c_source_count": 0, "token_contains_raw_target_ir_json_count": 0, "token_contains_expected_output_count": 0, "unsupported_has_targetir_count": 0, "unsupported_has_expected_output_count": 0, "arbitrary_project_claim_count": 0, "production_support_claim_count": 0}
    license_report = {"license_audit_passed": True}
    parse = {"algorithm_parse_success_rate": 1.0}
    token = {"algorithm_to_token_overall_success_rate": 1.0, "token_schema_valid_rate": 1.0}
    roundtrip = {"token_to_ir_success_rate": 1.0}
    compiler = {"backend_claim_safe": True}
    family = {"function_array_success_rate": 0.921, "counter_machine_project_witness_success_rate": 0.986, "bounded_regression_clean": True}
    heldout = {"heldout_algorithm_variant_success_rate": 0.906, "variant_generalization_passed": True}
    sym = {"algorithm_symbiote_positive": True}
    comfort = {"comfort_zone_audit_passed": True}
    result = readiness(dataset, audit, license_report, parse, token, roundtrip, {}, compiler, family, heldout, sym, comfort)
    assert result["arbitrary_project_parsing_completed"] is False
    assert result["formal_turing_completeness_proven"] is False
    assert result["natural_language_layer_completed"] is False
    assert result["production_support"] is False
    assert result["ready_for_official_release"] is False

