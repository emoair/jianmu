from jianmu.self_learning.darwinforge.mirror_landing_readiness import build_mirror_landing_readiness, classify_mirror_landing


def test_mirror_landing_classification_does_not_mark_repair_as_preexisting(tmp_path) -> None:
    classification = classify_mirror_landing(
        tmp_path,
        {"mirror_preexisting_landing_found": False, "mirror_docs_only_detected": False, "mirror_records_only_detected": False, "landing_status": "partial_landing"},
        True,
        {"mirror_runtime_probe_passed": True},
        {"mirror_negative_boundary_audit_passed": True},
        {"mirror_redqueen_integration_passed": True},
    )
    assert classification["landing_classification"] == "partial_landing_repaired"
    assert classification["preexisting_runtime_landing_found"] is False


def test_mirror_landing_readiness_keeps_production_false(tmp_path) -> None:
    result = build_mirror_landing_readiness(tmp_path, {"redqueen_truth_gate_passed": True, "landing_classification": "partial_landing_repaired", "mirror_runtime_probe_passed": True, "mirror_negative_boundary_audit_passed": True})
    assert result["recommended_claim_level"] == "mirror_alternating_freeze_landing_repaired"
    assert result["production_function_support_completed"] is False
    assert result["redqueen_autonomous_governance_completed"] is False

