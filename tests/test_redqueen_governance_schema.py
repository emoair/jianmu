from jianmu.self_learning.darwinforge.redqueen_governance_schema import RedQueenAllocatorConfig, RedQueenDryRunConfig


def test_redqueen_governance_schema():
    assert RedQueenAllocatorConfig().max_weight == 5.0
    assert RedQueenDryRunConfig().events == 20_000
