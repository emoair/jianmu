from jianmu.self_learning.darwinforge.human_review_pack_readiness import build_human_review_pack_readiness


def test_readiness_requires_replay_clean(tmp_path):
    result = build_human_review_pack_readiness(tmp_path, True, True, _interface(), 300, {"replay_validation_completed": True, "replay_sample_count": 300, "replay_fail_count": 1}, _alignment(), _bundle(), _precheck())
    assert result["recommended_claim_level"] == "review_pack_partial_needs_replay_fix"


def test_readiness_keeps_production_support_false(tmp_path):
    result = build_human_review_pack_readiness(tmp_path, True, True, _interface(), 300, _replay(), _alignment(), _bundle(), _precheck())
    assert result["production_function_support_completed"] is False
    assert result["production_array_support_completed"] is False
    assert result["production_recursion_support_completed"] is False
    assert result["ready_for_official_release"] is False


def test_no_expression_oracle_import():
    import inspect
    import jianmu.self_learning.darwinforge.trace_replay_validator as module
    assert "expression_oracle" not in inspect.getsource(module)


def test_no_external_api_calls():
    import inspect
    import jianmu.self_learning.darwinforge.reviewer_evidence_bundle_builder as module
    source = inspect.getsource(module).lower()
    assert "openai" not in source and "requests." not in source


def test_real_promotion_disabled(tmp_path):
    result = build_human_review_pack_readiness(tmp_path, True, True, _interface(), 300, _replay(), _alignment(), _bundle(), _precheck())
    assert result["production_dry_run_executed"] is False


def _interface():
    return {"interface_landing_review_completed": True, "atomic_policy_interfaces_valid": True, "builder_interfaces_valid": True, "extended_ir_interfaces_valid": True, "extended_emitter_interfaces_valid": True, "compiler_interfaces_valid": True, "template_bypass_detected": False, "marker_ir_direct_compile_detected": False}


def _replay():
    return {"replay_validation_completed": True, "replay_sample_count": 300, "replay_success_rate": 1.0, "replay_fail_count": 0, "workers_requested": 16, "workers_used": 16, "downgrade_reason": ""}


def _alignment():
    return {"alignment_review_completed": True, "samples_with_ir_json": 300, "samples_with_emitted_c": 300, "samples_with_stdout_pair": 300, "artifact_sha256_manifest_generated": True}


def _bundle():
    return {"reviewer_evidence_bundle_generated": True, "artifact_sha256_manifest_generated": True}


def _precheck():
    return {"production_dry_run_executed": False, "ready_for_production_dry_run_candidate": True}

