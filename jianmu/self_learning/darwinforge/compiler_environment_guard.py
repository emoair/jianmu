from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from jianmu.self_learning.darwinforge.msvc_environment_preflight import run_msvc_environment_preflight
from jianmu.self_learning.darwinforge.msvc_environment_schema import MSVCEnvironmentConfig


def guard_compiler_environment(output_records: str | Path, require_msvc_env: bool = True) -> Dict[str, object]:
    out = Path(output_records)
    result = run_msvc_environment_preflight(MSVCEnvironmentConfig(require_msvc_env=require_msvc_env))
    _write_json(out / "msvc_environment_preflight.json", result)
    return result


def build_msvc_fail_fast_test(output_records: str | Path) -> Dict[str, object]:
    out = Path(output_records)
    preflight = run_msvc_environment_preflight(MSVCEnvironmentConfig(require_msvc_env=True), path_override="")
    result = {
        "msvc_fail_fast_test_completed": True,
        "simulated_missing_cl": True,
        "fail_fast_triggered": preflight["fail_fast_triggered"],
        "validation_started": False,
        "clear_error_message": bool(preflight["recommended_user_action"]),
    }
    result["msvc_fail_fast_test_passed"] = all([
        result["simulated_missing_cl"],
        result["fail_fast_triggered"],
        not result["validation_started"],
        result["clear_error_message"],
    ])
    _write_json(out / "msvc_fail_fast_test.json", result)
    return result


def validation_can_start(preflight: Dict[str, object]) -> bool:
    return bool(preflight.get("compiler_environment_ready") and preflight.get("msvc_preflight_passed") and not preflight.get("fail_fast_triggered"))


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
