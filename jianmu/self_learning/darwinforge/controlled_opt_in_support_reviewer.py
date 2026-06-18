from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def build_reviewer_support_pack(output_records: str | Path, readiness_preview: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    pack = out / "reviewer_support_pack"
    pack.mkdir(parents=True, exist_ok=True)
    files = {
        "REVIEWER_README.md": _readme(readiness_preview),
        "SUPPORT_SCOPE_MATRIX.md": "# Support Scope Matrix\n\nSee `support_scope_matrix.json`; every subset requires explicit opt-in and keeps production_completed=false.\n",
        "UNSUPPORTED_BOUNDARY_MATRIX.md": "# Unsupported Boundary Matrix\n\nUnsafe and unsupported cases reject or classify before unsafe compiler use.\n",
        "FAILURE_TAXONOMY.md": "# Failure Taxonomy\n\nBlocking failures downgrade readiness and never permit production claims.\n",
        "VALIDATION_SUMMARY.md": f"# Validation Summary\n\nNegative events: {readiness_preview.get('negative_validation_events', 0)}\n\nPositive events: {readiness_preview.get('positive_validation_events', 0)}\n",
        "CLAIM_BOUNDARY_SUMMARY.md": "# Claim Boundary Summary\n\nThis is controlled opt-in support candidate evidence, not production support completed evidence.\n",
        "REVIEW_CHECKLIST.md": "- [ ] support scope is limited\n- [ ] unsupported boundaries reject safely\n- [ ] positive compiler validation is clean\n- [ ] trace pack is replayable\n- [ ] rollback keeps default blocked\n- [ ] no production overclaim\n",
    }
    manifest = {}
    for name, text in files.items():
        path = pack / name
        path.write_text(text, encoding="utf-8")
        manifest[name] = {"path": name, "size_bytes": path.stat().st_size}
    (pack / "artifact_sha256_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"reviewer_support_pack_generated": True, "reviewer_support_pack_path": str(pack), "artifact_sha256_manifest_generated": True}


def _readme(readiness: Dict[str, Any]) -> str:
    return (
        "# Controlled Opt-in Support Candidate Reviewer Pack\n\n"
        "This pack shows which bounded function, array, function-array, and structured-recursion shapes are support candidates under explicit opt-in.\n\n"
        "It does not prove production readiness, production support completion, formal Turing completeness, arbitrary project parsing, or natural language support.\n\n"
        "Review the positive trace for ExtendedIR / ExtendedEmitterC / compiler stdout evidence, the negative trace for blocked unsupported inputs, and rollback records for default-profile safety.\n\n"
        f"Recommended claim level: `{readiness.get('recommended_claim_level', 'pending')}`.\n"
    )
