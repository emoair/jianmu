from jianmu.self_learning.darwinforge.linguaforge_token_to_nl_teacher import token_to_nl_teacher_metrics
from jianmu.self_learning.darwinforge.linguaforge_nl_alpha_core import build_row


def test_token_to_nl_teacher_semantic_preservation():
    metrics = token_to_nl_teacher_metrics([build_row(i, 188) for i in range(500)])
    assert metrics["token_to_nl_semantic_preservation_rate"] >= 0.9
