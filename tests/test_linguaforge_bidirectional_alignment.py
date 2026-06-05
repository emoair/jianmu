from jianmu.self_learning.darwinforge.linguaforge_bidirectional_alignment import bidirectional_alignment_metrics
from jianmu.self_learning.darwinforge.linguaforge_nl_alpha_core import build_row


def test_bidirectional_alignment_preserves_semantic_hash():
    metrics = bidirectional_alignment_metrics([build_row(i, 188) for i in range(20)])
    assert metrics["semantic_hash_preservation_rate"] >= 0.9
    assert metrics["bidirectional_consistency_rate"] >= 0.82
