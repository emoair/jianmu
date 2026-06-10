from jianmu.self_learning.darwinforge.trace_replay_validator import _summary


def test_trace_replay_validator_detects_stdout_drift():
    result = _summary([{"replay_passed": False, "stdout_mismatch": True, "source_hash_drift": False, "policy_path_drift": False, "ir_kind_drift": False, "compile_failure": False, "timeout": False}], 1, 1)
    assert result["replay_stdout_mismatch_count"] == 1
    assert result["replay_fail_count"] == 1


def test_trace_replay_validator_detects_policy_path_drift():
    result = _summary([{"replay_passed": False, "stdout_mismatch": False, "source_hash_drift": False, "policy_path_drift": True, "ir_kind_drift": False, "compile_failure": False, "timeout": False}], 1, 1)
    assert result["replay_policy_path_drift_count"] == 1

