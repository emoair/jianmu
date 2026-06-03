from pathlib import Path

from jianmu.self_learning.darwinforge.full_compile_50k_preflight import write_full_compile_50k_preflight


def test_full_compile_50k_preflight(tmp_path: Path) -> None:
    payload = write_full_compile_50k_preflight(tmp_path)
    assert "vswhere_found" in payload
    assert "cl_zs_test_passed" in payload
    assert "preflight_passed" in payload
