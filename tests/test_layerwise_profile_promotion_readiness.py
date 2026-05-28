from jianmu.self_learning.darwinforge.layerwise_profile_promotion_readiness import build_layerwise_profile_promotion_readiness, write_layerwise_profile_integrity


def test_layerwise_profile_readiness_no_real_promotion(tmp_path):
    integrity = write_layerwise_profile_integrity(tmp_path)
    readiness = build_layerwise_profile_promotion_readiness(
        tmp_path,
        {"promotion_probe_completed": True, "profiles_attempted": [], "profiles_completed": [], "profiles": []},
        {"all_promotion_probe_gates_passed": True, "capability_gate_passed": True, "stage_gate_passed": True, "boundary_gate_passed": True, "compiler_gate_passed": True, "persistence_gate_passed": True, "resource_gate_passed": True, "integrity_gate_passed": True},
        {"layerwise_resource_overhead_acceptable": True},
        {"compiler_verified_correct_rate": 1.0},
        {"cross_process_reload_passed": True},
        integrity,
    )
    assert readiness["real_promotion_enabled"] is False
    assert readiness["profile_is_default_runtime"] is False
    assert readiness["ready_for_default_profile_dry_run"] is True


def test_layerwise_profile_readiness_no_turing_complete_claim(tmp_path):
    readiness = build_layerwise_profile_promotion_readiness(tmp_path, {}, {}, {}, {}, {}, {"real_promotion_enabled": False, "profile_is_default_runtime": False})
    assert "turing" not in readiness["recommended_claim_level"].lower()


def test_integrity_real_promotion_disabled(tmp_path):
    integrity = write_layerwise_profile_integrity(tmp_path)
    assert integrity["real_promotion_enabled"] is False
    assert integrity["profile_is_default_runtime"] is False
