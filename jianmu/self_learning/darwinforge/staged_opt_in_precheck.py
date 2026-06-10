from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def run_staged_opt_in_precheck(output_records: str | Path, review_clean: bool) -> Dict[str, object]:
    blockers: List[str] = [] if review_clean else ["controlled_review_not_clean"]
    result = {
        "staged_opt_in_executed": False,
        "staged_opt_in_enabled": False,
        "ready_for_staged_opt_in_candidate": review_clean,
        "required_before_staged_opt_in": [
            "human approval of controlled review records",
            "explicit staged opt-in design review",
            "separate v1.0.7 candidate branch",
        ],
        "blockers_before_staged_opt_in": blockers,
        "required_human_review_items": [
            "default profile contamination audit",
            "Windows records write isolation audit",
            "targeted replay manifest",
            "rollback stress review",
        ],
        "suggested_next_branch": "v1.0.7-staged-opt-in-profile-candidate",
        "production_ready": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
    }
    _write_json(Path(output_records) / "staged_opt_in_precheck.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
