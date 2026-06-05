from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row, roundtrip_metrics


def test_csystems_roundtrip_eval():
    assert roundtrip_metrics([build_csystems_row(i) for i in range(100)])["token_to_ir_success_rate"] == 1.0
