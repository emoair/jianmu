from jianmu.self_learning.darwinforge.algorithm_variant_symbiote_probe import variant_symbiote_metrics


def test_variant_symbiote_probe_positive():
    assert variant_symbiote_metrics()["variant_symbiote_positive"] is True
