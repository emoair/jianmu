from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


DANGEROUS_TERMS = ("pointer-heavy", "malloc", "file IO", "multi-file", "natural language", "arbitrary user code")


def audit_support_scope_overclaim(source_records: str | Path, output_records: str | Path) -> Dict[str, Any]:
    data = json.loads((Path(source_records) / "support_scope_matrix.json").read_text(encoding="utf-8"))
    rows = data.get("subsets", [])
    unsupported_in_allowed: List[str] = []
    missing_opt_in = 0
    missing_evidence = 0
    production_claim = False
    default_reachable = False
    for row in rows:
        allowed = " ".join(str(item) for item in row.get("allowed_shapes", []))
        forbidden = " ".join(str(item) for item in row.get("forbidden_shapes", []))
        unsupported_in_allowed.extend(term for term in DANGEROUS_TERMS if term.lower() in allowed.lower())
        production_claim = production_claim or bool(row.get("production_completed"))
        default_reachable = default_reachable or bool(row.get("default_profile_reachable"))
        missing_opt_in += 0 if row.get("requires_explicit_opt_in") is True else 1
        evidence = " ".join(str(item) for item in row.get("verified_by_records", []))
        if "v1_0_7_2" not in evidence and "v1_0_8" not in evidence:
            missing_evidence += 1
        if "unsupported" not in forbidden.lower() and not row.get("forbidden_shapes"):
            unsupported_in_allowed.append(f"{row.get('subset')}:missing_forbidden_shapes")
    result = {
        "support_scope_audit_completed": True,
        "overclaim_detected": bool(unsupported_in_allowed or production_claim or default_reachable or missing_opt_in or missing_evidence),
        "unsupported_feature_in_scope_count": len(unsupported_in_allowed),
        "production_completed_claim_detected": production_claim,
        "default_reachable_claim_detected": default_reachable,
        "missing_explicit_opt_in_requirement_count": missing_opt_in,
        "missing_evidence_reference_count": missing_evidence,
        "support_scope_audit_passed": not bool(unsupported_in_allowed or production_claim or default_reachable or missing_opt_in or missing_evidence),
        "notes": unsupported_in_allowed,
    }
    _write_json(Path(output_records) / "support_scope_overclaim_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
