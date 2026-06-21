from jianmu.self_learning.darwinforge.redqueen_real_landing_schema import RedQueenEnduranceConfig, build_real_landing_design


def test_redqueen_real_landing_schema():
    cfg = RedQueenEnduranceConfig()
    assert cfg.cycles == 3
    assert cfg.wall_clock_min_hours == 6.0


def test_redqueen_real_landing_design_forbids_default_profile_control():
    design = build_real_landing_design()
    assert design["redqueen_does_not_control_default_profile"] is True
    assert design["real_landing_design_passed"] is True
