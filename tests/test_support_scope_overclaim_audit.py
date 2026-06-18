import json

from jianmu.self_learning.darwinforge.support_scope_overclaim_audit import audit_support_scope_overclaim


def _write_scope(path, allowed, production=False):
    path.mkdir(parents=True, exist_ok=True)
    (path / "support_scope_matrix.json").write_text(json.dumps({"subsets": [{"subset": "function", "allowed_shapes": allowed, "forbidden_shapes": ["unsupported"], "production_completed": production, "default_profile_reachable": False, "requires_explicit_opt_in": True, "verified_by_records": ["records/v1_0_7_2_coverage_replay/"]}]}), encoding="utf-8")


def test_support_scope_overclaim_audit_blocks_pointer_claim(tmp_path):
    source = tmp_path / "source"
    _write_scope(source, ["pointer-heavy function"])
    result = audit_support_scope_overclaim(source, tmp_path / "out")
    assert result["support_scope_audit_passed"] is False


def test_support_scope_overclaim_audit_blocks_production_completed(tmp_path):
    source = tmp_path / "source"
    _write_scope(source, ["pure int function"], production=True)
    result = audit_support_scope_overclaim(source, tmp_path / "out")
    assert result["production_completed_claim_detected"] is True
