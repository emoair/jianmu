from jianmu.self_learning.darwinforge.longhaul_plateau_detector import detect_plateau
from jianmu.self_learning.darwinforge.longhaul_rolling_metrics import build_rolling_windows


def test_plateau_detector_outputs_slope(tmp_path):
    result = detect_plateau(build_rolling_windows(["longhaul_redqueen_hydrabudget_symbiote"]), tmp_path)
    assert "top1_slope" in result
    assert "candidate_miss_slope" in result
    assert isinstance(result["marginal_gain_curve"], list)
