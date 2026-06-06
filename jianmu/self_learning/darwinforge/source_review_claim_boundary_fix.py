from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


ALLOWED_AFTER_V1_0_5 = [
    "bounded production runtime baseline",
    "experimental active FunctionIR / ArrayIR / RecursiveIR bridge if validation passes",
    "frontier evidence preserved",
    "V1.0 package evidence provenance repaired",
    "50K accounted summary evidence unless raw trace pack is present",
    "real IR to C to compiler trace for v1.0.5 subset if generated",
]

FORBIDDEN_AFTER_V1_0_5 = [
    "production function support completed",
    "production array support completed",
    "production recursion support completed",
    "arbitrary project parsing completed",
    "formal Turing completeness proven",
    "production readiness",
    "solved program synthesis",
    "natural language layer completed",
]


def write_claim_boundary_fix_report(output_records: str | Path) -> Dict[str, Any]:
    result = {
        "claim_boundary_fix_completed": True,
        "allowed_after_v1_0_5": ALLOWED_AFTER_V1_0_5,
        "forbidden_after_v1_0_5": FORBIDDEN_AFTER_V1_0_5,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "real_promotion_disabled": True,
        "default_profile_unchanged": True,
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "claim_boundary_fix_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result

