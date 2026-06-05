from jianmu.self_learning.darwinforge.linguaforge_nl_roundtrip_eval import nl_roundtrip_eval


def test_linguaforge_nl_roundtrip_eval():
    metrics = nl_roundtrip_eval([])
    assert metrics["roundtrip_eval_completed"]
    assert metrics["nl_to_token_to_ir_roundtrip_success_rate"] >= 0.82
