import json

from jianmu.self_learning.darwinforge.default_profile_contamination_audit import run_default_profile_contamination_audit


def test_default_profile_contamination_audit_detects_shadow_route(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "production_profile_dry_run_readiness.json").write_text(json.dumps({"staged_opt_in_enabled": True}), encoding="utf-8")
    result = run_default_profile_contamination_audit(source, tmp_path / "out")
    assert result["staged_opt_in_enabled_detected"] is True
    assert result["default_profile_contamination_detected"] is True


def test_default_profile_contamination_audit_passes_clean_default(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "production_profile_dry_run_readiness.json").write_text(json.dumps({
        "user_facing_enabled": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
    }), encoding="utf-8")
    result = run_default_profile_contamination_audit(source, tmp_path / "out")
    assert result["default_profile_contamination_detected"] is False
