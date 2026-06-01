from jianmu.self_learning.darwinforge.longhaul_rolling_metrics import build_rolling_windows, summarize_rolling_metrics


def test_rolling_metrics_no_cherrypick_summary(tmp_path):
    windows = build_rolling_windows(["v0_9_23_reference", "longhaul_redqueen_hydrabudget_symbiote"])
    summary = summarize_rolling_metrics(windows, tmp_path)
    assert "best_window" in summary
    assert "final_window" in summary
    assert "mean_across_windows" in summary
    assert "no cherry" in summary["no_cherry_pick_summary"].lower()
