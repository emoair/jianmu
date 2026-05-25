import json

from jianmu.self_learning.darwinforge.arithmetic_baseline_ablation_audit import audit_baseline_ablation


def test_baseline_ablation_audit_marks_missing_not_faked(tmp_path):
    records = tmp_path / "records"
    records.mkdir()
    (records / "arithmetic_training_metrics.json").write_text(json.dumps({
        "actual_eval_iterated_count": 10,
        "actual_heldout_iterated_count": 5,
        "heldout_supported_success_rate": 0.95,
        "unsupported_false_accept_rate": 0.0,
        "trap_false_accept_rate": 0.0,
        "future_domain_supported_accept_rate": 0.0,
        "near_ood_supported_accept_rate": 0.0,
    }), encoding="utf-8")
    result = audit_baseline_ablation(records, tmp_path / "out")
    assert result["baseline_gap_verified"] is False
    assert any(row["method"] == "random_router" and row["executed"] is False for row in result["methods"])
