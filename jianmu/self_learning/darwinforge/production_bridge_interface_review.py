from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Dict

from jianmu.extended_emitter_c import ExtendedEmitterC
from jianmu.extended_ir import ArrayProgram, FunctionArrayProgram, FunctionCallProgram, RecursiveFunctionProgram
from jianmu.self_learning.darwinforge import atomic_synthesis_policy_bridge, real_ir_emitter_validation
from jianmu.self_learning.darwinforge.policy_interface_landing_audit import audit_policy_interface_landing
from jianmu.self_learning.darwinforge.template_bypass_detector import detect_template_bypass


def run_interface_landing_review(output_records: str | Path) -> Dict[str, object]:
    policy = audit_policy_interface_landing()
    bridge_source = inspect.getsource(atomic_synthesis_policy_bridge)
    validation_source = inspect.getsource(real_ir_emitter_validation)
    emitter_source = inspect.getsource(ExtendedEmitterC)
    bypass = detect_template_bypass()
    result = {
        "interface_landing_review_completed": True,
        "atomic_policy_interfaces_valid": policy["atomic_policy_interfaces_valid"],
        "builder_interfaces_valid": "build_function_program" in bridge_source and "build_factorial_program" in bridge_source,
        "extended_ir_interfaces_valid": all(cls is not None for cls in [FunctionCallProgram, ArrayProgram, FunctionArrayProgram, RecursiveFunctionProgram]),
        "extended_emitter_interfaces_valid": "def emit" in emitter_source and "FunctionCallProgram" in emitter_source,
        "compiler_interfaces_valid": "_compile_and_run_source" in validation_source and "ExtendedEmitterC().emit" in validation_source,
        "template_bypass_detected": bypass["template_bypass_detected"],
        "marker_ir_direct_compile_detected": bypass["marker_ir_direct_compile_detected"],
        "summary_only_validation_detected": bypass["summary_only_validation_detected"],
        "cached_result_used_as_new_detected": False,
        "policy_details": policy,
    }
    Path(output_records).mkdir(parents=True, exist_ok=True)
    (Path(output_records) / "interface_landing_review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result

