from jianmu.self_learning.darwinforge.reviewer_evidence_bundle_builder import build_reviewer_evidence_bundle


def test_reviewer_evidence_bundle_builder(tmp_path):
    result = build_reviewer_evidence_bundle(tmp_path, {"trace_replay_validation": {}, "interface_landing_review": {}})
    assert result["reviewer_evidence_bundle_generated"] is True
    assert (tmp_path / "reviewer_evidence_bundle" / "REVIEWER_README.md").exists()

