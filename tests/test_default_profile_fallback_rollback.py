from jianmu.self_learning.darwinforge.default_profile_fallback_rollback import run_fallback_rollback_dryrun


def test_default_profile_fallback_rollback(tmp_path):
    result = run_fallback_rollback_dryrun(tmp_path, {"production_config_modified": False, "actual_default_profile_unchanged": True})
    assert result["fallback_rollback_gate_passed"] is True
    assert result["rollback_does_not_modify_production_config"] is True
