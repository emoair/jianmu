from jianmu.self_learning.darwinforge.controlled_opt_in_longhaul_schema import ControlledOptInLonghaulConfig


def test_longhaul_schema():
    config = ControlledOptInLonghaulConfig()
    assert config.wall_clock_min_hours == 8.0
    assert config.minimum_real_validation_events == 120000
