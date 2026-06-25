from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable


SECURITY_KEYWORDS = ("access denied", "permission denied", "winerror 5", "winerror 32", "360", "antivirus", "defender", "quarantine")


def classify_security_interference(text: str, *, artifact_missing: bool = False, permission_error: bool = False) -> Dict[str, object]:
    lower = text.lower()
    suspected = artifact_missing or permission_error or any(keyword in lower for keyword in SECURITY_KEYWORDS)
    return {
        "security_interference_detected": suspected,
        "artifact_quarantine_suspected": artifact_missing,
        "permission_denied": permission_error or "permission denied" in lower or "access denied" in lower or "winerror 5" in lower,
        "executable_blocked": "blocked" in lower or "quarantine" in lower,
    }


def audit_security_interference(output_records: str | Path, rows: Iterable[Dict[str, object]]) -> Dict[str, object]:
    rows = list(rows)
    detected = sum(1 for row in rows if row.get("security_interference_detected"))
    artifact_missing = sum(1 for row in rows if row.get("artifact_missing_after_compile"))
    permission = sum(1 for row in rows if row.get("permission_error"))
    blocked = sum(1 for row in rows if row.get("exe_blocked"))
    result = {
        "security_interference_audit_completed": True,
        "security_interference_detector_enabled": True,
        "antivirus_or_360_suspected": detected > 0,
        "security_interference_detected_count": detected,
        "artifact_quarantine_suspected_count": artifact_missing,
        "permission_denied_count": permission,
        "executable_blocked_count": blocked,
        "compile_artifact_missing_count": artifact_missing,
        "whitelist_recovery_detected": detected == 0,
        "security_interference_classification_clean": detected == 0,
        "notes": "No current security interference was detected during the short backend validation." if detected == 0 else "Security interference was classified separately from compiler correctness.",
    }
    _write_json(Path(output_records) / "security_interference_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

