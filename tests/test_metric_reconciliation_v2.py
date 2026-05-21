from jianmu.self_learning.darwinforge.metric_reconciliation_v2 import MetricRecord, reconcile_metric_records


def _record(**overrides):
    payload = {
        "run_id": "run-a",
        "mode": "xlarge",
        "seed": 42,
        "evaluator_name": "global_beam_v2",
        "phase": "before_guard",
        "split_id": "split-a",
        "train_sample_count": 2200,
        "eval_sample_count": 600,
        "ood_sample_count": 200,
        "sample_hashes": {"train": "a", "eval": "b", "ood": "c"},
        "global_correct_targetir_in_beam_rate": 0.8167,
        "candidate_space_failure_rate": 0.1833,
        "ood_false_accept_rate": 0.335,
        "arithmetic_supported_retention_rate": 1.0,
        "source_record_path": "records/test.json",
        "baseline_mode": "xlarge",
        "baseline_run_id": "run-a",
    }
    payload.update(overrides)
    return MetricRecord(**payload)


def test_metric_reconciliation_detects_guard_wrong_baseline():
    result = reconcile_metric_records([_record(phase="after_guard", baseline_mode="large")])
    assert not result["metric_consistency_passed"]
    assert any(item["type"] == "guard_wrong_baseline" for item in result["inconsistencies"])


def test_metric_reconciliation_detects_before_after_inversion():
    before = _record(phase="before_guard", ood_false_accept_rate=0.2)
    after = _record(phase="after_guard", ood_false_accept_rate=0.4)
    result = reconcile_metric_records([before, after])
    assert any(item["type"] == "before_after_inversion" for item in result["inconsistencies"])


def test_metric_reconciliation_passes_consistent_records():
    before = _record(phase="before_guard", ood_false_accept_rate=0.335)
    after = _record(phase="after_guard", ood_false_accept_rate=0.235)
    result = reconcile_metric_records([before, after])
    assert result["metric_consistency_passed"]
    assert result["inconsistency_count"] == 0
