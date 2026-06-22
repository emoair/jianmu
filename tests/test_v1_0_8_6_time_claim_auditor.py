import json

from jianmu.self_learning.darwinforge.v1_0_8_6_time_claim_auditor import audit_v1_0_8_6_time_claim


def test_v1_0_8_6_time_claim_auditor_detects_missing_timestamps(tmp_path):
    root = tmp_path / "records"
    (root / "cycles" / "cycle_0").mkdir(parents=True)
    (root / "endurance_summary.json").write_text(json.dumps({"wall_clock_hours": 8.0, "cycles_completed": 8, "total_events": 300000, "real_compiler_invocations": 239432}), encoding="utf-8")
    (root / "cycles" / "cycle_0" / "cycle_execution_metrics.json").write_text(json.dumps({"wall_clock_hours": 1.0}), encoding="utf-8")
    result = audit_v1_0_8_6_time_claim(root)
    assert result["v1_0_8_6_endurance_claim_downgraded"] is True
    assert result["v1_0_8_6_endurance_claim_accepted"] is False
