from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def build_approval_gate_verdict(output_records: str | Path, audits: Dict[str, Dict[str, Any]], candidate_ready: bool = True) -> Dict[str, Any]:
    out = Path(output_records)
    signoff = out / "REVIEW_SIGNOFF.md"
    signed = _signoff_approved(signoff)
    clean = all([
        audits["reviewer"].get("reviewer_pack_audit_passed"),
        audits["scope"].get("support_scope_audit_passed"),
        audits["unsupported"].get("unsupported_boundary_audit_passed"),
        audits["taxonomy"].get("failure_taxonomy_audit_passed"),
        audits["sampling"].get("evidence_sampling_passed"),
        audits["isolation"].get("windows_onedrive_isolation_passed"),
        candidate_ready,
    ])
    if not audits["isolation"].get("windows_onedrive_isolation_passed"):
        status = "blocked_by_records_isolation"
    elif not audits["scope"].get("support_scope_audit_passed"):
        status = "blocked_by_scope_overclaim"
    elif not audits["unsupported"].get("unsupported_boundary_audit_passed"):
        status = "blocked_by_unsupported_boundary_gap"
    elif not audits["sampling"].get("evidence_sampling_passed"):
        status = "blocked_by_evidence_sampling"
    elif clean and signed == "approved":
        status = "approved"
    elif clean and signed == "approved_with_notes":
        status = "approved_with_notes"
    elif clean:
        status = "approval_recommended"
    else:
        status = "not_approved"
    result = {
        "approval_gate_started": True,
        "approval_gate_completed": True,
        "reviewer_pack_audit_passed": audits["reviewer"].get("reviewer_pack_audit_passed"),
        "support_scope_audit_passed": audits["scope"].get("support_scope_audit_passed"),
        "unsupported_boundary_audit_passed": audits["unsupported"].get("unsupported_boundary_audit_passed"),
        "failure_taxonomy_audit_passed": audits["taxonomy"].get("failure_taxonomy_audit_passed"),
        "evidence_sampling_passed": audits["sampling"].get("evidence_sampling_passed"),
        "windows_onedrive_isolation_passed": audits["isolation"].get("windows_onedrive_isolation_passed"),
        "default_profile_unchanged": True,
        "explicit_opt_in_required": True,
        "real_promotion_enabled": False,
        "user_facing_enabled": False,
        "official_release_enabled": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "controlled_opt_in_support_candidate_ready": candidate_ready,
        "controlled_opt_in_support_approval_recommended": status == "approval_recommended",
        "controlled_opt_in_support_approved": status in {"approved", "approved_with_notes"},
        "human_signoff_required": status == "approval_recommended",
        "approval_status": status,
        "approval_notes": [] if clean else ["approval gate has blocking audit issues"],
        "blocking_issues": [] if clean else [status],
    }
    _write_json(out / "approval_gate_verdict.json", result)
    return result


def _signoff_approved(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace").lower()
    if "[x] approved_with_notes" in text:
        return "approved_with_notes"
    if "[x] approved" in text:
        return "approved"
    return ""


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
