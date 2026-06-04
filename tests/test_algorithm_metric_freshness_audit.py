from jianmu.self_learning.darwinforge.algorithm_metric_freshness_audit import detect_copied_metrics, metric_freshness_audit


def test_metric_freshness_detects_copied_v1_0_2_metrics(tmp_path):
    result = detect_copied_metrics({"a": 1}, {"a": 1}, "v1.0.2")
    assert result["copied_from_v1_0_2_detected"] is True
    assert result["metric_freshness_passed"] is False


def test_metric_freshness_detects_copied_v1_0_3_metrics(tmp_path):
    result = detect_copied_metrics({"a": 1}, {"a": 1}, "v1.0.3")
    assert result["copied_from_v1_0_3_detected"] is True
    assert result["metric_freshness_passed"] is False


def test_metric_freshness_current_run_passes(tmp_path):
    result = metric_freshness_audit(tmp_path / "v103", tmp_path / "out")
    assert result["algorithm_specific_eval_executed"] is True
    assert result["metric_freshness_passed"] is True
    assert result["copied_from_v1_0_3_detected"] is False
