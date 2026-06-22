from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, Tuple

from jianmu.self_learning.darwinforge.msvc_environment_schema import MSVCEnvironmentConfig, build_msvc_environment_record


DEFAULT_VCVARS64_CANDIDATES: Tuple[str, ...] = (
    r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat",
    r"C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat",
)


def run_msvc_environment_preflight(
    config: MSVCEnvironmentConfig | None = None,
    *,
    env: Dict[str, str] | None = None,
    path_override: str | None = None,
    vcvars64_candidates: Iterable[str] = DEFAULT_VCVARS64_CANDIDATES,
) -> Dict[str, object]:
    cfg = config or MSVCEnvironmentConfig()
    env_map = dict(os.environ if env is None else env)
    search_path = env_map.get("PATH", "") if path_override is None else path_override
    cl_path = shutil.which("cl.exe", path=search_path) or shutil.which("cl", path=search_path)
    link_path = shutil.which("link.exe", path=search_path) or shutil.which("link", path=search_path)
    cl_version = _can_run_version(cl_path, cfg.timeout_seconds, env_map) if cl_path else False
    link_version = _can_run_version(link_path, cfg.timeout_seconds, env_map) if link_path else False
    vcvars_initialized = bool(env_map.get("VCToolsInstallDir") or env_map.get("VSINSTALLDIR") or env_map.get("WindowsSdkDir"))
    candidates = tuple(str(Path(item)) for item in vcvars64_candidates if Path(item).exists())
    vswhere = shutil.which("vswhere.exe", path=search_path) or shutil.which("vswhere", path=search_path)
    shell_warning = ""
    if not cl_path:
        shell_warning = "MSVC cl.exe is not visible in PATH; ordinary PowerShell often needs vcvars64.bat first."
    reason = ""
    if not cl_path:
        reason = "cl.exe not found in PATH"
    elif not link_path:
        reason = "link.exe not found in PATH"
    elif not cl_version:
        reason = "cl.exe version command failed"
    elif not link_version:
        reason = "link.exe version command failed"
    result = build_msvc_environment_record(
        cl_found=bool(cl_path),
        link_found=bool(link_path),
        cl_version_detected=cl_version,
        link_version_detected=link_version,
        vcvars_initialized=vcvars_initialized,
        vswhere_detected=bool(vswhere),
        vcvars64_candidate_paths=candidates,
        shell_warning=shell_warning,
        fail_fast_reason=reason,
    )
    if not cfg.require_msvc_env:
        result["fail_fast_triggered"] = False
    return result


def _can_run_version(path: str | None, timeout_seconds: int, env: Dict[str, str]) -> bool:
    if not path:
        return False
    try:
        proc = subprocess.run([path], capture_output=True, text=True, timeout=timeout_seconds, env=env)
    except (OSError, subprocess.SubprocessError):
        return False
    output = f"{proc.stdout}\n{proc.stderr}".lower()
    return "microsoft" in output or proc.returncode == 0
