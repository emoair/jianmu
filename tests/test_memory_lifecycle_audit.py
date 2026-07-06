import json

from jianmu.self_learning.darwinforge.memory_lifecycle_audit import audit_v1_0_8_8_4_memory_pressure


def test_memory_lifecycle_audit(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "backend6h_validation_summary.json").write_text(json.dumps({"backend6h_validation_passed": True}), encoding="utf-8")
    (source / "memory_queue_guard.json").write_text(json.dumps({"queue_peak_size": 1}), encoding="utf-8")
    result = audit_v1_0_8_8_4_memory_pressure(source, tmp_path / "out")
    assert result["memory_pressure_audit_completed"] is True
    assert result["v1_0_8_8_4_memory_clean_claim_downgraded"] is True
