from jianmu.self_learning.darwinforge.trace_shard_size_cap import audit_trace_shard_size_cap


def test_trace_shard_size_cap_rotates_before_50mb(tmp_path) -> None:
    (tmp_path / "trace.jsonl").write_text("x\n", encoding="utf-8")
    result = audit_trace_shard_size_cap(tmp_path, hard_fail_threshold_bytes=50)
    assert result["oversized_shard_count"] == 0
    assert result["trace_shard_size_cap_passed"] is True
