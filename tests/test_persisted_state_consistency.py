from jianmu.self_learning.darwinforge.persisted_state_consistency import check_persisted_state_consistency


def test_persisted_state_consistency_passes_with_small_delta():
    original = {"current_supported_retention_rate": 1.0, "overall_ood_false_accept_rate": 0.0}
    reloaded = {
        "current_supported_retention_rate": 0.99,
        "overall_ood_false_accept_rate": 0.01,
        "no_label_inference_passed": True,
        "forbidden_field_access_count": 0,
        "over_rejection_detected": False,
    }
    assert check_persisted_state_consistency(original, reloaded)["persisted_state_consistency_passed"] is True


def test_persisted_state_consistency_fails_with_large_delta():
    original = {"current_supported_retention_rate": 1.0, "overall_ood_false_accept_rate": 0.0}
    reloaded = {
        "current_supported_retention_rate": 0.80,
        "overall_ood_false_accept_rate": 0.40,
        "no_label_inference_passed": True,
        "forbidden_field_access_count": 0,
        "over_rejection_detected": False,
    }
    assert check_persisted_state_consistency(original, reloaded)["persisted_state_consistency_passed"] is False
