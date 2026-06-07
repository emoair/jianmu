from jianmu.self_learning.darwinforge.template_bypass_detector import detect_template_bypass


def test_template_bypass_detector_flags_direct_template_compile():
    result = detect_template_bypass()
    assert "template_bypass_detected" in result
    assert result["template_bypass_detected"] is False


def test_template_bypass_detector_allows_extended_ir_emitter_path():
    result = detect_template_bypass()
    assert result["extended_ir_emitter_path_allowed"] is True
    assert result["marker_ir_direct_compile_detected"] is False

