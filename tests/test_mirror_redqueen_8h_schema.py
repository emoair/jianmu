from jianmu.self_learning.darwinforge.mirror_redqueen_8h_schema import CYCLE_DESIGNS, MirrorRedQueen8hConfig


def test_mirror_redqueen_8h_schema() -> None:
    cfg = MirrorRedQueen8hConfig()
    assert cfg.planned_wall_clock_hours == 8.0
    assert cfg.cycles == 8
    assert len(CYCLE_DESIGNS) == 8

