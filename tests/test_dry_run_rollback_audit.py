from jianmu.self_learning.darwinforge.dry_run_rollback_audit import run_dry_run_rollback_audit


def test_dry_run_rollback_audit_disables_shadow_profile(tmp_path):
    result = run_dry_run_rollback_audit(tmp_path)
    assert result["rollback_test_passed"] is True
    assert result["shadow_profile_disable_test_passed"] is True
    assert result["production_flags_after_rollback_false"] is True
