from __future__ import annotations

from typing import Any, Dict, Tuple

from jianmu.extended_emitter_c import ExtendedEmitterC
from jianmu.self_learning.darwinforge.function_array_ir_bridge import build_array_program, build_function_array_program, build_function_program
from jianmu.self_learning.darwinforge.production_path_reconciliation_schema import EXPERIMENTAL_POLICIES, policy_metadata
from jianmu.self_learning.darwinforge.recursion_ir_bridge import build_factorial_program


def build_extended_target(policy: str, features: Dict[str, Any]) -> Tuple[str, str, str, Dict[str, Any]]:
    meta = policy_metadata(policy)
    if not meta["supported"]:
        raise ValueError("unsupported extended policy")
    value = int((features.get("signed_numbers") or [7])[0])
    if policy == "canonical_function_targetir":
        program = build_function_program(value)
    elif policy == "canonical_array_targetir":
        program = build_array_program(value)
    elif policy == "canonical_function_array_targetir":
        program = build_function_array_program(value)
    elif policy == "canonical_structured_recursion_targetir":
        n = max(0, min(8, value))
        program = build_factorial_program(n)
        meta["recursion_mode"] = program.recursion_mode
        meta["production_recursion_support"] = False
    else:
        raise ValueError("unsupported extended policy")
    source = ExtendedEmitterC().emit(program)
    canonical = f"{EXPERIMENTAL_POLICIES[policy]}({value})"
    return canonical, source, program.expected_stdout or "", meta

