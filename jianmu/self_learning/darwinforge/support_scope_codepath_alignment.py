from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


EXPECTED = {
    "function": "FunctionCallProgram",
    "array": "ArrayProgram",
    "function_array": "FunctionArrayProgram",
    "structured_recursion": "RecursiveFunctionProgram",
}


def check_support_scope_codepath_alignment(source_records: str | Path, output_records: str | Path) -> Dict[str, Any]:
    source = Path(source_records)
    matrix = json.loads((source / "support_scope_matrix.json").read_text(encoding="utf-8"))
    readiness = json.loads((source / "controlled_opt_in_support_readiness.json").read_text(encoding="utf-8"))
    subsets = {row["subset"]: row for row in matrix.get("subsets", [])}
    result = {"support_scope_alignment_completed": True, "missing_codepath_count": 0, "overclaimed_scope_count": 0, "notes": []}
    for subset in EXPECTED:
        row = subsets.get(subset, {})
        aligned = bool(row) and row.get("requires_explicit_opt_in") is True and row.get("default_profile_reachable") is False and row.get("production_completed") is False
        result[f"{subset}_scope_aligned" if subset != "structured_recursion" else "structured_recursion_scope_aligned"] = aligned
        if not aligned:
            result["missing_codepath_count"] += 1
            result["notes"].append(f"{subset}: scope row missing or unsafe")
    result["unsupported_scope_blocked"] = readiness.get("negative_validation_passed") is True and readiness.get("unsafe_compile_invoked_count") == 0
    result["support_scope_codepath_aligned"] = (
        result["missing_codepath_count"] == 0
        and result["overclaimed_scope_count"] == 0
        and result["unsupported_scope_blocked"]
    )
    _write_json(Path(output_records) / "support_scope_codepath_alignment.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
