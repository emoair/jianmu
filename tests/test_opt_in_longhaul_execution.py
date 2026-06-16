from jianmu.self_learning.darwinforge.opt_in_longhaul_execution import _heartbeat


def test_longhaul_execution_records_guard_heartbeat():
    row = _heartbeat(5000, 1.0)
    assert row["event_index"] == 5000
    assert row["guard_failure"] is False
