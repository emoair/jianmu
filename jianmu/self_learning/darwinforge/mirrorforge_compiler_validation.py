from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_v2_compiler_validation import build_redqueen_v2_compiler_validation


def run_mirrorforge_compiler_validation(output_records: str | Path, target: int = 5000, compile_worker_count: int = 16) -> Dict[str, Any]:
    out = Path(output_records)
    metrics = build_redqueen_v2_compiler_validation(out, supported_spot=target, boundary_spot=target, compile_worker_count=compile_worker_count)
    mirror = {
        "compiler_validation_completed": metrics["compiler_validation_completed"],
        "real_compiler_invocation_count": metrics["real_compiler_invocation_count"],
        "compiler_verified_correct_rate": metrics["compiler_verified_correct_rate"],
        "wrong_stdout_count": metrics["wrong_stdout_count"],
        "timeout_count": metrics["timeout_count"],
        "permission_error_count": metrics["permission_error_count"],
        "cleanup_failure_count": metrics["cleanup_failure_count"],
        "boundary_compiler_misroute_count": metrics["boundary_compiler_misroute_count"],
        "future_domain_compiled_count": metrics["future_domain_compiled_count"],
        "unsupported_compiled_count": metrics["unsupported_compiled_count"],
        "trap_compiled_count": metrics["trap_compiled_count"],
        "recursion_compiled_count": metrics["recursion_compiled_count"],
        "pointer_compiled_count": metrics["pointer_compiled_count"],
        "io_compiled_count": metrics["io_compiled_count"],
        "backend_type": metrics["backend_type"],
        "compiler_name": metrics["compiler_name"],
    }
    _write_json(out / "mirrorforge_compiler_validation.json", mirror)
    src = out / "redqueen_v2_compiler_trace_manifest.json"
    if src.exists():
        shutil.copyfile(src, out / "mirrorforge_compiler_trace_manifest.json")
    return mirror


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
