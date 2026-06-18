from jianmu.self_learning.darwinforge.approval_gate_verdict import build_approval_gate_verdict


def _audits():
    return {
        "reviewer": {"reviewer_pack_audit_passed": True},
        "scope": {"support_scope_audit_passed": True},
        "unsupported": {"unsupported_boundary_audit_passed": True},
        "taxonomy": {"failure_taxonomy_audit_passed": True},
        "sampling": {"evidence_sampling_passed": True},
        "isolation": {"windows_onedrive_isolation_passed": True},
    }


def test_approval_gate_requires_human_signoff_for_approved(tmp_path):
    result = build_approval_gate_verdict(tmp_path, _audits(), candidate_ready=True)
    assert result["approval_status"] == "approval_recommended"
    assert result["controlled_opt_in_support_approved"] is False


def test_approval_gate_allows_approval_recommended_without_signoff(tmp_path):
    result = build_approval_gate_verdict(tmp_path, _audits(), candidate_ready=True)
    assert result["controlled_opt_in_support_approval_recommended"] is True
    assert result["human_signoff_required"] is True
