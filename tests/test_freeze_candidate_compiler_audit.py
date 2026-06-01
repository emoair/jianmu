from jianmu.self_learning.darwinforge.freeze_candidate_evidence_matrix import collect_version_evidence
from jianmu.self_learning.darwinforge.freeze_candidate_compiler_audit import run_compiler_audit


def test_compiler_audit_accounts_real_cl_validation(tmp_path):
    evidence = collect_version_evidence("records", ["v0_9_18_2", "v0_9_20", "v0_9_23"])
    audit = run_compiler_audit(evidence, tmp_path)
    assert audit["total_real_compiler_invocations_accounted"] >= 27800
    assert audit["compiler_audit_passed"] is True
    assert audit["future_domain_compiled_total"] == 0
