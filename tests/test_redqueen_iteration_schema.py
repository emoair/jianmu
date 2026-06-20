from jianmu.self_learning.darwinforge.redqueen_iteration_schema import BASE_EVENT_DISTRIBUTION, RedQueenIterationConfig, STILL_NOT_PROVEN_ITERATION


def test_redqueen_iteration_schema():
    cfg = RedQueenIterationConfig()
    assert cfg.iteration_events == 60000
    assert sum(BASE_EVENT_DISTRIBUTION.values()) == 60000
    assert "RedQueen autonomous governance completed" in STILL_NOT_PROVEN_ITERATION
