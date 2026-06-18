from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict


REQUIRED_REVIEWER_FILES = (
    "REVIEWER_README.md",
    "SUPPORT_SCOPE_MATRIX.md",
    "UNSUPPORTED_BOUNDARY_MATRIX.md",
    "FAILURE_TAXONOMY.md",
    "VALIDATION_SUMMARY.md",
    "CLAIM_BOUNDARY_SUMMARY.md",
    "REVIEW_CHECKLIST.md",
    "artifact_sha256_manifest.json",
)


def audit_reviewer_pack(source_records: str | Path, output_records: str | Path) -> Dict[str, Any]:
    pack = Path(source_records) / "reviewer_support_pack"
    missing = [name for name in REQUIRED_REVIEWER_FILES if not (pack / name).exists()]
    hashes_valid = False
    if (pack / "artifact_sha256_manifest.json").exists():
        try:
            json.loads((pack / "artifact_sha256_manifest.json").read_text(encoding="utf-8"))
            hashes_valid = True
        except json.JSONDecodeError:
            hashes_valid = False
    readme = (pack / "REVIEWER_README.md").read_text(encoding="utf-8", errors="replace") if (pack / "REVIEWER_README.md").exists() else ""
    result = {
        "reviewer_pack_found": pack.exists(),
        "reviewer_pack_complete": not missing,
        "reviewer_readme_clear": "not prove production readiness" in readme or "not production support" in readme or "does not prove production" in readme,
        "support_scope_matrix_present": (pack / "SUPPORT_SCOPE_MATRIX.md").exists(),
        "unsupported_boundary_matrix_present": (pack / "UNSUPPORTED_BOUNDARY_MATRIX.md").exists(),
        "failure_taxonomy_present": (pack / "FAILURE_TAXONOMY.md").exists(),
        "validation_summary_present": (pack / "VALIDATION_SUMMARY.md").exists(),
        "claim_boundary_summary_present": (pack / "CLAIM_BOUNDARY_SUMMARY.md").exists(),
        "review_checklist_present": (pack / "REVIEW_CHECKLIST.md").exists(),
        "artifact_sha256_manifest_present": (pack / "artifact_sha256_manifest.json").exists(),
        "reviewer_pack_hashes_valid": hashes_valid,
        "missing_files": missing,
    }
    result["reviewer_pack_audit_passed"] = all([
        result["reviewer_pack_found"],
        result["reviewer_pack_complete"],
        result["reviewer_readme_clear"],
        result["reviewer_pack_hashes_valid"],
    ])
    _write_json(Path(output_records) / "reviewer_pack_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
