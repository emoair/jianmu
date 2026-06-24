from jianmu.self_learning.darwinforge.mirror_frozen_lane_integrity_audit import audit_frozen_lane_integrity


def test_frozen_lane_integrity_rejects_mutation(tmp_path) -> None:
    cycles = [{"execution": {"frozen_mutation_attempt_count": 1, "rejected_frozen_mutation_count": 1}, "mirror": {"frozen_lane_hash_before_after_match": True}}]
    result = audit_frozen_lane_integrity(tmp_path, cycles)
    assert result["frozen_lane_integrity_audit_passed"] is True
    assert result["frozen_mutation_allowed_count"] == 0

