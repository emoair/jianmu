import json

from jianmu.self_learning.darwinforge.redqueen_truth_gate import run_redqueen_truth_gate


def test_redqueen_truth_gate_requires_time_integrity_repair(tmp_path) -> None:
    records = tmp_path / "records"
    time_dir = records / "v1_0_8_6_1_time_integrity"
    time_dir.mkdir(parents=True)
    (time_dir / "time_integrity_readiness.json").write_text(json.dumps({"recommended_claim_level": "time_integrity_repaired_and_short_wallclock_validated", "minimum_satisfied_by": "actual_monotonic_elapsed", "heartbeat_contract_passed": True, "lifecycle_recheck_passed": True}), encoding="utf-8")
    (time_dir / "v1_0_8_6_time_claim_audit.json").write_text(json.dumps({"v1_0_8_6_endurance_claim_downgraded": True}), encoding="utf-8")
    result = run_redqueen_truth_gate(tmp_path / "out", records, tmp_path / "missing", time_dir)
    assert result["time_integrity_repair_confirmed"] is True
    assert result["v1_0_8_6_old_8h_claim_downgraded"] is True


def test_redqueen_truth_gate_rejects_old_8h_claim(tmp_path) -> None:
    records = tmp_path / "records"
    time_dir = records / "v1_0_8_6_1_time_integrity"
    time_dir.mkdir(parents=True)
    (time_dir / "time_integrity_readiness.json").write_text(json.dumps({"recommended_claim_level": "time_integrity_repaired_and_short_wallclock_validated", "minimum_satisfied_by": "actual_monotonic_elapsed", "heartbeat_contract_passed": True, "lifecycle_recheck_passed": True}), encoding="utf-8")
    (time_dir / "v1_0_8_6_time_claim_audit.json").write_text(json.dumps({"v1_0_8_6_endurance_claim_downgraded": False}), encoding="utf-8")
    result = run_redqueen_truth_gate(tmp_path / "out", records, tmp_path / "missing", time_dir)
    assert result["redqueen_truth_gate_passed"] is False
    assert "old_v1_0_8_6_8h_claim_not_downgraded" in result["blockers"]

