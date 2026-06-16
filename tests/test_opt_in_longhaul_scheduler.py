from jianmu.self_learning.darwinforge.controlled_opt_in_longhaul_schema import ControlledOptInLonghaulConfig
from jianmu.self_learning.darwinforge.opt_in_longhaul_scheduler import build_longhaul_schedule


def test_longhaul_scheduler_requires_8h_config():
    result = build_longhaul_schedule(ControlledOptInLonghaulConfig(), {"function": 1})
    assert result["requires_8h_config"] is True
