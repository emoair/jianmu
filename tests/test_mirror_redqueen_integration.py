from jianmu.self_learning.darwinforge.mirror_cosymbiosis_metrics import build_mirror_cosymbiosis_metrics
from jianmu.self_learning.darwinforge.mirror_redqueen_integration import integrate_mirror_metrics_with_redqueen


def test_mirror_redqueen_integration_forbids_default_profile_change(tmp_path) -> None:
    metrics = build_mirror_cosymbiosis_metrics(tmp_path)
    result = integrate_mirror_metrics_with_redqueen(tmp_path, metrics)
    assert result["mirror_metrics_read_by_redqueen"] is True
    assert result["redqueen_modifies_default_profile"] is False
    assert result["redqueen_enables_real_promotion"] is False

