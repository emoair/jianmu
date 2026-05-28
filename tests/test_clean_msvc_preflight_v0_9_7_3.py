from __future__ import annotations

from jianmu.self_learning.darwinforge.clean_msvc_preflight import run_clean_msvc_preflight


def test_clean_msvc_preflight_records_vcvars_and_cl(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        "jianmu.self_learning.darwinforge.clean_msvc_preflight.detect_msvc_and_path_compilers",
        lambda: {"vswhere_found": True, "vcvars64_found": True, "vcvars64_path": "vcvars64.bat", "cl_bv_test_passed": True, "cl_version_text_tail": "cl", "path_cl_found": False},
    )
    monkeypatch.setattr("jianmu.self_learning.darwinforge.clean_msvc_preflight._stale_process_summary", lambda: {"stale_cl_process_count": 0, "stale_link_process_count": 0, "stale_python_process_count": 0, "stale_process_summary": []})
    result = run_clean_msvc_preflight(tmp_path, tmp_path)
    assert result["vcvars64_found"] is True
    assert result["cl_bv_test_passed"] is True


def test_clean_msvc_preflight_does_not_kill_processes() -> None:
    import inspect
    import jianmu.self_learning.darwinforge.clean_msvc_preflight as module

    source = inspect.getsource(module)
    assert "Stop-Process" not in source
    assert "taskkill" not in source
