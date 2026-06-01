from jianmu.self_learning.darwinforge.freeze_candidate_architecture_audit import run_architecture_audit


def test_architecture_audit_charter_compliance(tmp_path):
    audit = run_architecture_audit(tmp_path)
    assert audit["architecture_charter_exists"] is True
    assert audit["symbiote_trunk_not_sole_truth_verifier"] is True
    assert audit["architecture_audit_passed"] is True
