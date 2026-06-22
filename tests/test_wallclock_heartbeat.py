from jianmu.self_learning.darwinforge.wallclock_heartbeat import HeartbeatWriter


def test_wallclock_heartbeat_records_span(tmp_path):
    writer = HeartbeatWriter(tmp_path / "heartbeat.jsonl", interval_seconds=300, interval_events=10000)
    writer.maybe_write(total_events=0, force=True)
    writer.maybe_write(total_events=1, force=True)
    result = writer.contract(actual_elapsed_seconds=10)
    assert result["heartbeat_records_written"] == 2
    assert result["heartbeat_contract_passed"] is True
