from jianmu.self_learning.darwinforge.coverage_expansion_schema import CoverageExpansionConfig


def test_coverage_expansion_schema():
    cfg = CoverageExpansionConfig()
    targets = cfg.target_counts()
    assert cfg.wall_clock_min_hours == 4.0
    assert cfg.replay_workers == 16
    assert sum(targets.values()) == 165000
