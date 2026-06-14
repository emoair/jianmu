from jianmu.self_learning.darwinforge.staged_opt_in_config import build_staged_opt_in_config


def test_staged_opt_in_config_writes_claim_boundary(tmp_path):
    result = build_staged_opt_in_config(tmp_path)
    assert result["default_profile_unchanged"] is True
    assert result["claim_boundary"]["production_function_support_completed"] is False
