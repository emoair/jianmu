from jianmu.self_learning.darwinforge.live_object_growth_audit import audit_live_object_growth


def test_live_object_growth_audit_detects_growth(tmp_path) -> None:
    result = audit_live_object_growth(tmp_path, 1000, 3000, tolerance_ratio=0.1)
    assert result["live_object_growth_audit_completed"] is True
    assert result["live_object_growth_bounded"] is False
