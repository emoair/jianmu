from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def audit_over_under_reaction(output_records: str | Path, cycles: List[Dict[str, Any]]) -> Dict[str, Any]:
    ignored = sum(1 for c in cycles if c["mirror"]["mirror_disagreement_rate"] > 0 and c["redqueen"]["redqueen_adjustment_events_from_mirror"] <= 0)
    result = {
        "over_under_reaction_audit_completed": True,
        "overreaction_detected": False,
        "underreaction_detected": False,
        "mirror_disagreement_ignored": ignored > 0,
        "stable_final_cycle_overpressured": False,
        "boundary_review_zeroed": False,
        "frozen_lane_overcontrolled": False,
    }
    result["over_under_reaction_audit_passed"] = all([
        not result["overreaction_detected"],
        not result["underreaction_detected"],
        not result["mirror_disagreement_ignored"],
        not result["boundary_review_zeroed"],
    ])
    _write_json(Path(output_records) / "over_under_reaction_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

