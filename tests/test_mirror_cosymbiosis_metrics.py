from jianmu.self_learning.darwinforge.mirror_cosymbiosis_metrics import build_mirror_cosymbiosis_metrics


def test_mirror_cosymbiosis_metrics_feed_redqueen(tmp_path) -> None:
    result = build_mirror_cosymbiosis_metrics(tmp_path, 100)
    assert result["metrics_feed_redqueen"] is True
    assert result["cosymbiosis_metrics_passed"] is True

