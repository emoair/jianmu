from pathlib import Path

from jianmu.self_learning.darwinforge.full_compile_50k_postflight import write_full_compile_50k_postflight


def test_full_compile_50k_postflight(tmp_path: Path) -> None:
    payload = write_full_compile_50k_postflight(tmp_path)
    assert "postflight_passed" in payload
    assert "stale_cl_process_count" in payload
    assert "known_security_process_detected" in payload
