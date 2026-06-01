from jianmu.self_learning.darwinforge.freeze_candidate_evidence_matrix import collect_version_evidence


def test_freeze_candidate_evidence_matrix_collects_versions():
    evidence = collect_version_evidence("records", ["v0_9_17", "v0_9_20", "v0_9_23"])
    assert evidence["best_version"] == "v0_9_23"
    assert evidence["best_top1"] == 0.9301
    assert evidence["best_candidate_miss"] == 0.0278
    assert len(evidence["top1_progression"]) == 3
