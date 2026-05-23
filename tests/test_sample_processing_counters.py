from jianmu.self_learning.darwinforge.sample_processing_counters import SampleProcessingCounters


def test_sample_counters_detect_reported_actual_mismatch():
    counters = SampleProcessingCounters("xlarge", reported_train_count=10, actual_train_iterated_count=5)
    result = counters.to_dict()
    assert result["count_match_passed"] is False
    assert result["synthetic_summary_detected"] is True


def test_sample_counters_detect_zero_loop():
    counters = SampleProcessingCounters("xlarge", reported_train_count=10, actual_train_iterated_count=0)
    result = counters.to_dict()
    assert result["suspicious_zero_loop_detected"] is True
    assert result["blocking_issue"] is True
