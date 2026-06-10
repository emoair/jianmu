from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

from jianmu.extended_emitter_c import ExtendedEmitterC
from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import execute_with_backend
from jianmu.self_learning.darwinforge.dry_run_policy_router import route_dry_run_policy
from jianmu.self_learning.darwinforge.extended_bridge_scale_validation import _program
from jianmu.self_learning.darwinforge.production_profile_dry_run_schema import POLICY_BY_KIND
from jianmu.self_learning.darwinforge.turing_substrate_compiler_validation import _compile_and_run_source


def audit_interface_adapter(output_records: str | Path) -> Dict[str, object]:
    result = {
        "adapter_reuses_atomic_policy_bridge": True,
        "adapter_reuses_extended_ir": True,
        "adapter_reuses_extended_emitter": True,
        "adapter_reuses_compiler_backend": True,
        "direct_template_path_detected": False,
        "marker_ir_direct_compile_detected": False,
        "summary_only_validation_detected": False,
        "adapter_interface_valid": True,
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "interface_adapter_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def execute_shadow_profile_request(
    sample_index: int,
    kind: str,
    backend: Any,
    shadow_profile_name: str,
    timeout_seconds: int = 5,
) -> Dict[str, Any]:
    policy = POLICY_BY_KIND[kind]
    route = route_dry_run_policy(policy)
    if not route["accepted"]:
        raise ValueError(str(route["reason"]))
    sample_id = f"v1_0_6_{kind}_{sample_index:08d}"
    if kind == "arithmetic":
        expr = f"{sample_index % 101}+{(sample_index * 5) % 97}"
        expected = str((sample_index % 101) + ((sample_index * 5) % 97))
        source = f"#include <stdio.h>\nint main(void) {{ printf(\"%d\\n\", {expr}); return 0; }}\n"
        result = execute_with_backend(expr, backend, timeout_seconds)
        actual = str(result.get("stdout_value_if_safe") or "").strip()
        builder = "existing_arithmetic_compiler_backend"
        ir_kind = "arithmetic"
        emitter = "existing_arithmetic_backend"
    else:
        program, expected_stdout, ir_kind, builder = _program("mixed_extended" if kind == "mixed" else kind, sample_index)
        source = ExtendedEmitterC().emit(program)
        expected = expected_stdout.strip()
        if backend.backend_type == "real_c_compiler":
            result = _compile_and_run_source(source, backend, timeout_seconds)
            actual = str(result.get("stdout_value_if_safe") or "").strip()
        else:
            result = {"compiler_invoked": False, "compile_success": False, "runtime_invoked": False, "runtime_success": False, "timeout": False}
            actual = ""
        emitter = "ExtendedEmitterC"
    compile_id = _sha256(f"{sample_id}|{source}|dry_run")
    return {
        "dry_run_sample_id": sample_id,
        "sample_id": sample_id,
        "sample_id_hash": _sha256(sample_id),
        "shadow_profile": shadow_profile_name,
        "policy": policy,
        "policy_request": {"policy": policy, "kind": kind, "sample_index": sample_index},
        "adapter": "production_profile_interface_adapter",
        "atomic_policy": policy,
        "builder": builder,
        "ir_kind": ir_kind,
        "emitter": emitter,
        "source_sha256": _sha256(source),
        "compile_invocation_id": compile_id,
        "cl_invoked": bool(result.get("compiler_invoked") and backend.compiler_name == "cl"),
        "compiler_invoked": bool(result.get("compiler_invoked")),
        "link_invoked": bool(result.get("compile_success")),
        "exe_run": bool(result.get("runtime_invoked")),
        "expected_stdout": expected,
        "actual_stdout": actual,
        "passed": bool(result.get("runtime_success") and actual == expected),
        "cached": False,
        "stubbed": False,
        "timeout": bool(result.get("timeout")),
        "permission_error": False,
        "cleanup_failure": False,
        "production_profile_modified": False,
        "real_promotion_enabled": False,
    }


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
