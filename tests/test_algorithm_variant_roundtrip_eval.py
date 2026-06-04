from jianmu.self_learning.darwinforge.algorithm_variant_generator import build_variant_row
from jianmu.self_learning.darwinforge.algorithm_variant_roundtrip_eval import roundtrip_metrics


def test_variant_roundtrip_eval():
    result = roundtrip_metrics([build_variant_row("pilot", i) for i in range(100)])
    assert result["token_to_ir_success_rate"] == 1.0
    assert result["variant_token_to_candidate_success_rate"] == 1.0
