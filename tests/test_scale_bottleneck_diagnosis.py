from jianmu.self_learning.darwinforge.scale_bottleneck_diagnosis import compute_cross_scale_metrics, diagnose_scale_bottlenecks


def test_bottleneck_diagnosis_scale_limited():
    result = diagnose_scale_bottlenecks([
        _run("small", global_rate=0.1, stable=10, ood=0.1),
        _run("medium", global_rate=0.15, stable=30, ood=0.1),
    ])
    assert result["scale_limited_likely"] is True


def test_bottleneck_diagnosis_promotion_limited():
    result = diagnose_scale_bottlenecks([
        _run("small", keep_local=5, colony=5, stable=100, shadow_promote=0),
        _run("medium", keep_local=8, colony=8, stable=200, shadow_promote=0),
    ])
    assert result["promotion_limited_likely"] is True


def test_bottleneck_diagnosis_routing_limited():
    result = diagnose_scale_bottlenecks([
        _run("small", global_rate=0.2, stable=20),
        _run("medium", global_rate=0.2, stable=50),
    ])
    assert result["routing_limited_likely"] is True


def test_bottleneck_diagnosis_ood_limited():
    result = diagnose_scale_bottlenecks([_run("small", ood=0.4)])
    assert result["ood_limited_likely"] is True


def test_bottleneck_diagnosis_resource_limited():
    run = _run("small", active=512, stable=1)
    run["config"] = {"max_total_active_roots": 512}
    result = diagnose_scale_bottlenecks([run])
    assert result["resource_limited_likely"] is True


def test_cross_scale_metrics():
    metrics = compute_cross_scale_metrics([_run("small", runtime=10), _run("medium", runtime=20)])
    assert "runtime_per_100_samples" in metrics
    assert "global_beam_trend" in metrics


def _run(label, global_rate=0.1, stable=0, nourished=0, keep_local=0, colony=1, shadow_promote=0, ood=0.0, active=1, runtime=1.0):
    return {
        "scale_label": label,
        "train_sample_count": 100,
        "eval_sample_count": 50,
        "ood_sample_count": 50,
        "runtime_seconds": runtime,
        "global_correct_targetir_in_beam_rate_after_shadow": global_rate,
        "stable_root_count": stable,
        "nourished_root_count": nourished,
        "keep_local_colony_count": keep_local,
        "colony_count": colony,
        "shadow_promote_candidate_count": shadow_promote,
        "ood_false_accept_after_shadow": ood,
        "toxic_event_count": int(ood * 100),
        "total_active_roots": active,
    }
