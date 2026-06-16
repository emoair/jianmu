from jianmu.self_learning.darwinforge.opt_in_longhaul_coverage_review import run_longhaul_coverage_review


def test_longhaul_coverage_review_flags_repeated_shape_risk(tmp_path):
    rows = [{"policy": "p", "category": "function", "ir_kind": "i", "source_sha256": "s", "compiler_invoked": True, "builder": "b"}]
    result = run_longhaul_coverage_review(tmp_path, rows, minimum_unique=9896, target_unique=12000)
    assert result["repeated_shape_risk_level"] == "medium"
