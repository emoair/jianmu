from jianmu.self_learning.darwinforge.security_interference_detector import classify_security_interference


def test_security_interference_detector_classifies_permission_block() -> None:
    result = classify_security_interference("Permission denied")
    assert result["security_interference_detected"] is True
    assert result["permission_denied"] is True


def test_security_interference_detector_classifies_missing_artifact() -> None:
    result = classify_security_interference("", artifact_missing=True)
    assert result["artifact_quarantine_suspected"] is True

