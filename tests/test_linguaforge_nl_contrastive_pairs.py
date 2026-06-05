from jianmu.self_learning.darwinforge.linguaforge_nl_contrastive_pairs import naturalness_metrics


def test_linguaforge_nl_contrastive_pairs():
    metrics = naturalness_metrics([])
    assert metrics["contrastive_nl_pair_success_rate"] >= 0.8
