from jianmu.self_learning.darwinforge.opt_in_heldout_validation_set import build_heldout_validation_set


def test_heldout_validation_set_is_not_training_set(tmp_path):
    result = build_heldout_validation_set(tmp_path, "profile")
    assert result["no_model_training"] is True
    assert result["no_weight_update"] is True


def test_heldout_validation_set_reuses_existing_generators(tmp_path):
    result = build_heldout_validation_set(tmp_path, "profile")
    assert result["source_from_existing_generators"] is True
    assert result["reused_existing_logic"] is True
