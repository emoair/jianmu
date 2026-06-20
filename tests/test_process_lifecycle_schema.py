from jianmu.self_learning.darwinforge.process_lifecycle_schema import ProcessLifecycleConfig, STILL_NOT_PROVEN_LIFECYCLE


def test_process_lifecycle_schema():
    cfg = ProcessLifecycleConfig()
    assert cfg.idle_grace_seconds == 30
    assert cfg.events == 20000
    assert "RedQueen autonomous governance completed" in STILL_NOT_PROVEN_LIFECYCLE
