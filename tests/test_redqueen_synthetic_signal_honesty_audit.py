from jianmu.self_learning.darwinforge.redqueen_synthetic_signal_honesty_audit import audit_synthetic_signal_honesty


def test_synthetic_signal_honesty_blocks_real_failure_claim():
    result = audit_synthetic_signal_honesty(
        [{"injection": {"injections": [{"weak_signal_is_synthetic": True, "affects_real_compiler": False}]}}],
        {"compiler_verified_correctness_rate": 1.0, "wrong_stdout_count": 0},
    )
    assert result["honesty_audit_passed"] is True
    assert result["synthetic_signal_claimed_as_real_failure"] is False
