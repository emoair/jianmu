from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.mirrorforge_compiler_validation import run_mirrorforge_compiler_validation


def run_codecartographer_compiler_validation(output_records: str | Path, target: int = 5000, compile_worker_count: int = 16) -> Dict[str, Any]:
    out = Path(output_records)
    base = run_mirrorforge_compiler_validation(out, target=target, compile_worker_count=compile_worker_count)
    run_label = f"primary_{compile_worker_count}"
    if not _clean(base) and compile_worker_count != 8:
        base = run_mirrorforge_compiler_validation(out, target=target, compile_worker_count=8)
        run_label = "fallback_8"
    result = {
        "run_label": run_label,
        "compiler_validation_completed": base["compiler_validation_completed"],
        "real_compiler_invocation_count": base["real_compiler_invocation_count"],
        "compiler_verified_correctness_rate": base["compiler_verified_correct_rate"],
        "wrong_stdout_count": base["wrong_stdout_count"],
        "timeout_count": base["timeout_count"],
        "permission_error_count": base["permission_error_count"],
        "cleanup_failure_count": base["cleanup_failure_count"],
        "boundary_compiler_misroute_count": base["boundary_compiler_misroute_count"],
        "future_domain_compiled_count": base["future_domain_compiled_count"],
        "unsupported_compiled_count": base["unsupported_compiled_count"],
        "trap_compiled_count": base["trap_compiled_count"],
        "recursion_compiled_count": base["recursion_compiled_count"],
        "pointer_compiled_count": base["pointer_compiled_count"],
        "io_compiled_count": base["io_compiled_count"],
        "backend_type": base["backend_type"],
        "compiler_name": base["compiler_name"],
    }
    _write_json(out / "codecartographer_compiler_validation.json", result)
    manifest = out / "mirrorforge_compiler_trace_manifest.json"
    if manifest.exists():
        shutil.copyfile(manifest, out / "codecartographer_compiler_trace_manifest.json")
    return result


def _clean(base: Dict[str, Any]) -> bool:
    return base.get("compiler_verified_correct_rate", 0.0) >= 0.99 and all(
        base.get(key, 0) == 0
        for key in [
            "wrong_stdout_count",
            "timeout_count",
            "permission_error_count",
            "cleanup_failure_count",
            "boundary_compiler_misroute_count",
            "future_domain_compiled_count",
        ]
    )


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
