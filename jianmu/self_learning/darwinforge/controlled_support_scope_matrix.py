from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def build_support_scope_matrix(output_records: str | Path) -> Dict[str, Any]:
    rows = [
        _row(
            "function",
            [
                "pure int function",
                "one / two / three int parameters",
                "return expression",
                "local variable precompute",
                "helper split",
                "static helper",
                "call from main",
                "deterministic stdout",
            ],
            [
                "function pointer",
                "variadic function",
                "external library call",
                "file IO",
                "malloc/free",
                "pointer-heavy parameters",
                "arbitrary user-defined function graph",
                "mutual recursion",
                "undefined behavior",
            ],
        ),
        _row(
            "array",
            [
                "fixed int array",
                "array length 1..32",
                "initializer pattern variation",
                "forward / reverse loop",
                "sum / max / min / second max",
                "count positive / count even",
                "simple write transform",
                "deterministic stdout",
            ],
            [
                "dynamic allocation",
                "out-of-bounds access",
                "pointer-heavy array manipulation",
                "multidimensional arrays unless already verified",
                "file input",
                "arbitrary array size from user",
                "unsafe indexing",
            ],
        ),
        _row(
            "function_array",
            [
                "helper function consumes supported array shape",
                "explicit bounded length if already supported",
                "return int aggregate",
                "deterministic stdout",
                "bridge path through ExtendedIR / ExtendedEmitterC",
            ],
            [
                "malloc arrays",
                "pointer-heavy mutation beyond verified bridge",
                "arbitrary pointer aliasing",
                "external input",
                "file IO",
                "multi-file",
            ],
        ),
        _row(
            "structured_recursion",
            [
                "factorial small n",
                "gcd small values",
                "countdown",
                "triangular number",
                "bounded structural recursion",
                "bounded depth validation",
                "watchdog required",
                "deterministic stdout",
            ],
            [
                "unbounded recursion",
                "mutual recursion",
                "unknown termination",
                "recursion over external input",
                "arbitrary recursive program synthesis",
                "proof of Turing completeness",
            ],
        ),
    ]
    result = {
        "support_scope_matrix_generated": True,
        "profile_name": "staged_opt_in_function_array_recursion_v1_0_7",
        "subsets": rows,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "support_scope_matrix.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _row(subset: str, allowed: List[str], forbidden: List[str]) -> Dict[str, Any]:
    return {
        "subset": subset,
        "support_candidate": True,
        "production_completed": False,
        "requires_explicit_opt_in": True,
        "default_profile_reachable": False,
        "verified_by_records": [
            "records/v1_0_7_staged_opt_in/",
            "records/v1_0_7_1_longhaul/",
            "records/v1_0_7_2_coverage_replay/",
        ],
        "allowed_shapes": allowed,
        "forbidden_shapes": forbidden,
        "failure_behavior": "reject unsupported shapes or classify them before compiler invocation",
        "trace_required": True,
    }
