from jianmu.self_learning.darwinforge.boundary_generalization_metrics import compute_boundary_generalization_metrics


def test_boundary_generalization_metrics_compute_all_rates():
    samples = [
        {"boundary_label": "current_supported"},
        {"boundary_label": "hard_ood"},
        {"boundary_label": "true_false_accept_trap"},
        {"boundary_label": "future_domain_candidate"},
        {"boundary_label": "near_ood_generalization_candidate"},
    ]
    decisions = [
        {"accepted_as_supported": True, "rejected": False},
        {"accepted_as_supported": False, "rejected": True},
        {"accepted_as_supported": False, "rejected": True},
        {"accepted_as_supported": False, "rejected": False, "future_buffered": True},
        {"accepted_as_supported": False, "rejected": False, "quarantined": True},
    ]
    metrics = compute_boundary_generalization_metrics(samples, decisions, {"after_metrics": {"overall_ood_false_accept_rate": 0.0}})
    assert metrics["current_supported_retention_rate"] == 1.0
    assert metrics["hard_ood_rejection_rate"] == 1.0
    assert "delta_ood_false_accept" in metrics


def test_report_contains_chinese_annotations():
    import pathlib

    path = pathlib.Path("docs/experiments/BOUNDARY_FREEBEAM_GENERALIZATION.md")
    assert "边界自由束泛化" in path.read_text(encoding="utf-8")
