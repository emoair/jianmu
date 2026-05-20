from jianmu.self_learning.darwinforge.metric_reconciliation import MetricScope, evaluate_ood_rows, reconcile_metrics


def test_metric_reconciliation_detects_ood_conflict():
    result = reconcile_metrics({"ood_false_accept_after": 0.0}, [{"scale": "small", "ood_false_accept_rate": 0.5}])

    assert result["ood_metric_consistency_passed"] is False
    assert result["inconsistent_metric_names"]


def test_metric_reconciliation_passes_consistent_metrics():
    result = reconcile_metrics({"ood_false_accept_after": 0.0}, [{"scale": "small", "ood_false_accept_rate": 0.0}])

    assert result["metric_consistency_passed"] is True


def test_ood_metric_definition_counts_false_accept():
    rows = [{"supported": False, "unsupported_pred": False}, {"supported": False, "unsupported_pred": True}]
    scope = MetricScope("ood", 2, "eval", "guard", "pop", "small")

    metrics = evaluate_ood_rows(rows, scope)

    assert metrics["ood_false_accept_rate"] == 0.5
