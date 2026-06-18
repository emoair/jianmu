from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


UNSUPPORTED_CASES = (
    "no explicit opt-in",
    "malformed opt-in flag",
    "disabled opt-in profile",
    "unknown policy",
    "unsupported function shape",
    "unsupported array shape",
    "unsupported recursion shape",
    "pointer-heavy request",
    "malloc/free request",
    "file IO request",
    "multi-file request",
    "arbitrary project parsing request",
    "natural language request",
    "external API request",
    "unbounded recursion",
    "mutual recursion",
    "production promotion request",
    "release request",
)


def build_unsupported_boundary_matrix(output_records: str | Path) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for case in UNSUPPORTED_CASES:
        expected = "reject" if case in {"unknown policy", "production promotion request", "release request"} else "classify_unsupported"
        if case in {"no explicit opt-in", "malformed opt-in flag", "disabled opt-in profile"}:
            expected = "reject"
        rows.append(
            {
                "unsupported_case": case,
                "expected_behavior": expected,
                "compile_invoked": False,
                "bridge_reachable": False if "opt-in" in case or case in {"unknown policy", "production promotion request", "release request"} else "controlled",
                "default_profile_modified": False,
                "real_promotion_enabled": False,
                "trace_required": True,
                "claim_boundary_note": "unsupported boundary evidence is not production support evidence",
            }
        )
    result = {"unsupported_boundary_matrix_generated": True, "unsupported_cases": rows}
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "unsupported_boundary_matrix.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
