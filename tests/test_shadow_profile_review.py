import json

from jianmu.self_learning.darwinforge.shadow_profile_review import run_shadow_profile_review


def test_shadow_profile_review_confirms_explicit_opt_in(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "shadow_profile_config.json").write_text(json.dumps({
        "shadow_profile_created": True,
        "profile_name": "production_shadow_dry_run_v1_0_6",
        "explicitly_opt_in": True,
        "default_profile": False,
        "real_promotion_enabled": False,
        "user_facing_enabled": False,
        "rollback_required": True,
        "audit_trace_required": True,
    }), encoding="utf-8")
    result = run_shadow_profile_review(source, tmp_path / "out")
    assert result["shadow_profile_valid"] is True
    assert result["explicit_opt_in_confirmed"] is True
