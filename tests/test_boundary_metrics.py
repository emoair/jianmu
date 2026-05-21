from jianmu.self_learning.darwinforge.boundary_metrics import compute_boundary_metrics


def test_boundary_metrics_compute_rejection_rates():
    samples = [{"boundary_label": "hard_ood"}, {"boundary_label": "hard_ood"}, {"boundary_label": "current_supported"}]
    results = [{"rejected": True}, {"accepted_as_supported": True}, {"accepted_as_supported": True}]
    metrics = compute_boundary_metrics(samples, results, [])
    assert metrics["hard_ood_rejection_rate"] == 0.5
    assert metrics["current_supported_retention_rate"] == 1.0
