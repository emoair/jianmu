from jianmu.self_learning.darwinforge.bounded_queue_backpressure import BoundedEvidenceQueue, write_bounded_queue_contract


def test_bounded_queue_backpressure_limits_queue_size(tmp_path) -> None:
    q = BoundedEvidenceQueue(maxsize=2)
    assert q.put({"a": 1}, correctness_evidence=False) is True
    assert q.put({"a": 2}, correctness_evidence=False) is True
    assert q.put({"a": 3}, correctness_evidence=False) is False
    q.drain()
    result = write_bounded_queue_contract(tmp_path, q, queue_maxsize=2)
    assert result["correctness_evidence_never_dropped"] is True
    assert result["bounded_queue_backpressure_passed"] is True
