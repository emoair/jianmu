from jianmu.self_learning.darwinforge.linguaforge_nl_paraphrase_builder import naturalness_metrics


def test_linguaforge_nl_paraphrase_builder():
    metrics = naturalness_metrics([])
    assert metrics["heldout_paraphrase_success_rate"] >= 0.82
