from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple


MSVC_RECOMMENDED_ACTION = "Run from x64 Native Tools Command Prompt for VS or initialize vcvars64.bat before running."


@dataclass(frozen=True)
class MSVCEnvironmentConfig:
    require_msvc_env: bool = True
    timeout_seconds: int = 10


def build_msvc_environment_record(
    *,
    cl_found: bool,
    link_found: bool,
    cl_version_detected: bool,
    link_version_detected: bool,
    vcvars_initialized: bool,
    vswhere_detected: bool,
    vcvars64_candidate_paths: Tuple[str, ...],
    shell_warning: str,
    fail_fast_reason: str = "",
) -> Dict[str, Any]:
    ready = cl_found and link_found and cl_version_detected and link_version_detected
    return {
        "msvc_preflight_started": True,
        "msvc_preflight_completed": True,
        "compiler_environment_ready": ready,
        "cl_found": cl_found,
        "link_found": link_found,
        "cl_version_detected": cl_version_detected,
        "link_version_detected": link_version_detected,
        "vcvars_initialized": vcvars_initialized,
        "vswhere_detected": vswhere_detected,
        "vcvars64_candidate_paths": list(vcvars64_candidate_paths),
        "shell_warning": shell_warning,
        "fail_fast_triggered": not ready,
        "fail_fast_reason": "" if ready else fail_fast_reason,
        "recommended_user_action": "" if ready else MSVC_RECOMMENDED_ACTION,
        "msvc_preflight_passed": ready,
    }
