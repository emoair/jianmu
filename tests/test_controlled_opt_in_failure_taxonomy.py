from jianmu.self_learning.darwinforge.controlled_opt_in_failure_taxonomy import build_failure_taxonomy


def test_failure_taxonomy_marks_default_leak_blocking(tmp_path):
    result = build_failure_taxonomy(tmp_path)
    rows = {row["failure_type"]: row for row in result["failures"]}
    assert rows["default_profile_contamination"]["severity"] == "blocking"
    assert rows["default_profile_contamination"]["production_claim_allowed"] is False
