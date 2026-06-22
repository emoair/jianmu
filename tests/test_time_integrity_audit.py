from jianmu.self_learning.darwinforge.time_integrity_audit import build_time_integrity_audit_summary


def test_time_integrity_audit():
    result = build_time_integrity_audit_summary({"v1_0_8_6_endurance_claim_downgraded": True}, {"code_audit_completed": True, "dangerous_time_patterns_found": ["x"]})
    assert result["time_integrity_audit_passed"] is True
    assert result["planned_as_actual_bug_found"] is True
