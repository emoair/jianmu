from jianmu.self_learning.darwinforge.turing_frontier_roundtrip_eval import run_roundtrip_eval


def test_turing_frontier_roundtrip_eval(tmp_path):
    result = run_roundtrip_eval(tmp_path)
    assert result["token_to_ir_success_rate"] > 0.99
    assert result["watchdog_evaluator_clean"] is True
    assert result["wrong_halting_class_count"] == 0
