from jianmu.self_learning.darwinforge.runtime_anomaly_diagnosis import diagnose_runtime_anomaly


def test_runtime_anomaly_detects_unrealistic_xlarge_runtime():
    report = diagnose_runtime_anomaly(
        {"runtime_seconds_total": 0.131871},
        {},
        {"reported_train_count": 50000, "reported_eval_count": 12000, "reported_external_ood_count": 15000, "actual_train_iterated_count": 0, "actual_eval_iterated_count": 0, "actual_external_ood_iterated_count": 0},
        {},
    )
    assert report["runtime_anomaly_detected"] is True
    assert report["anomaly_severity"] == "blocking"
