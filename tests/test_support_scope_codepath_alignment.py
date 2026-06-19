import json

from jianmu.self_learning.darwinforge.support_scope_codepath_alignment import check_support_scope_codepath_alignment


def test_support_scope_codepath_alignment(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    subsets = [{"subset": item, "requires_explicit_opt_in": True, "default_profile_reachable": False, "production_completed": False} for item in ["function", "array", "function_array", "structured_recursion"]]
    (source / "support_scope_matrix.json").write_text(json.dumps({"subsets": subsets}), encoding="utf-8")
    (source / "controlled_opt_in_support_readiness.json").write_text(json.dumps({"negative_validation_passed": True, "unsafe_compile_invoked_count": 0}), encoding="utf-8")
    result = check_support_scope_codepath_alignment(source, tmp_path / "out")
    assert result["support_scope_codepath_aligned"] is True
