from jianmu.self_learning.darwinforge.v0_9_14_readiness import build_v0_9_14_integrity


def test_v0_9_14_readiness_no_turing_complete_claim(tmp_path):
    integrity = build_v0_9_14_integrity(tmp_path, {"actual_default_profile_unchanged": True, "production_config_modified": False}, {"dataset_v2_audit_passed": True})
    assert integrity["real_promotion_enabled"] is False
    assert integrity["profile_is_default_runtime"] is False


def test_integrity_real_promotion_disabled(tmp_path):
    integrity = build_v0_9_14_integrity(tmp_path, {"actual_default_profile_unchanged": True, "production_config_modified": False}, {"dataset_v2_audit_passed": True})
    assert integrity["real_promotion_enabled"] is False
