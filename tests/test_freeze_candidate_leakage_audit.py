from jianmu.self_learning.darwinforge.freeze_candidate_evidence_matrix import collect_version_evidence
from jianmu.self_learning.darwinforge.freeze_candidate_leakage_audit import run_leakage_audit


def test_leakage_audit_summarizes_cross_version_contract(tmp_path):
    evidence = collect_version_evidence("records", ["v0_9_21", "v0_9_22", "v0_9_23"])
    audit = run_leakage_audit(evidence, tmp_path)
    assert audit["leakage_audit_passed"] is True
    assert audit["data_contract_clean"] is True
    assert audit["future_domain_in_train_current_count"] == 0
