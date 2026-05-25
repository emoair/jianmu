import json

from jianmu.self_learning.darwinforge.arithmetic_metric_provenance import audit_metric_provenance


def test_metric_provenance_detects_fixed_period_rule(tmp_path):
    records = tmp_path / "records"
    records.mkdir()
    (records / "arithmetic_training_metrics.json").write_text(json.dumps({
        "supported_candidate_hit_before": 0.8,
        "supported_candidate_hit_after": 0.95,
        "heldout_supported_success_rate": 0.95,
    }), encoding="utf-8")
    (records / "arithmetic_stage_metrics.json").write_text(json.dumps({"stages": []}), encoding="utf-8")
    result = audit_metric_provenance(records, tmp_path / "out")
    assert result["fixed_value_detected"] is True
    assert result["summary_only_detected"] is True
    assert result["metric_provenance_passed"] is False
