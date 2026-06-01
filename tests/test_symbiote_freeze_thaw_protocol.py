from jianmu.self_learning.darwinforge.symbiote_freeze_thaw_protocol import build_freeze_thaw_protocol


def test_freeze_thaw_protocol_disallows_default_profile_change(tmp_path):
    result = build_freeze_thaw_protocol(tmp_path)
    assert result["freeze_thaw_protocol_completed"] is True
    assert result["not_gan"] is True
    assert result["default_profile_changed"] is False
