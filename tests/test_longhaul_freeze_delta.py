from jianmu.self_learning.darwinforge.longhaul_freeze_delta import build_freeze_delta
from jianmu.self_learning.darwinforge.longhaul_rolling_metrics import build_rolling_windows, summarize_rolling_metrics


def test_freeze_candidate_delta(tmp_path):
    rolling = summarize_rolling_metrics(build_rolling_windows(["longhaul_redqueen_hydrabudget_symbiote"]), tmp_path)
    compiler = {"compiler_validation_clean": True, "real_compiler_invocation_count": 10}
    delta = build_freeze_delta(rolling, compiler, tmp_path)
    assert delta["strengthens_v1_0_freeze_candidate"] is True
    assert delta["weakens_v1_0_freeze_candidate"] is False
