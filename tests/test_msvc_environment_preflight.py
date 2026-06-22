import os

from jianmu.self_learning.darwinforge.msvc_environment_preflight import run_msvc_environment_preflight
from jianmu.self_learning.darwinforge.msvc_environment_schema import MSVCEnvironmentConfig


def _fake_tool(path, name):
    tool = path / f"{name}.bat"
    tool.write_text("@echo Microsoft fake tool\n", encoding="utf-8")
    return tool


def test_msvc_preflight_detects_cl(tmp_path):
    _fake_tool(tmp_path, "cl")
    _fake_tool(tmp_path, "link")
    env = dict(os.environ)
    env["PATH"] = str(tmp_path)
    result = run_msvc_environment_preflight(MSVCEnvironmentConfig(), env=env)
    assert result["cl_found"] is True
    assert result["link_found"] is True
    assert result["msvc_preflight_passed"] is True


def test_msvc_preflight_fail_fast_when_cl_missing():
    result = run_msvc_environment_preflight(MSVCEnvironmentConfig(), path_override="")
    assert result["compiler_environment_ready"] is False
    assert result["fail_fast_triggered"] is True
    assert "vcvars64.bat" in result["recommended_user_action"]
