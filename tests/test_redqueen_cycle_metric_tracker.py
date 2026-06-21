from jianmu.self_learning.darwinforge.redqueen_cycle_metric_tracker import derive_post_metrics, write_cycle_metrics


def test_redqueen_cycle_metric_tracker_records_pre_post_metrics(tmp_path):
    metrics = {"categories": [{"category": "function", "success_rate": 1.0}]}
    written = write_cycle_metrics(tmp_path, 1, metrics, "cycle_pre_metrics.json")
    assert written["metrics_snapshot_created"] is True
    post = derive_post_metrics(metrics, {"actual_category_distribution": {"function": 5}, "actual_difficulty_distribution": {"function": 2}, "actual_review_allocation": {"function": 1.0}})
    assert post["categories"][0]["category_event_count"] == 5
