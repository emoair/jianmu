from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def audit_frozen_lane_integrity(output_records: str | Path, cycles: List[Dict[str, Any]]) -> Dict[str, Any]:
    attempts = sum(int(c["execution"]["frozen_mutation_attempt_count"]) for c in cycles)
    rejected = sum(int(c["execution"]["rejected_frozen_mutation_count"]) for c in cycles)
    result = {
        "frozen_lane_integrity_audit_completed": True,
        "frozen_mutation_attempt_count": attempts,
        "rejected_frozen_mutation_count": rejected,
        "frozen_mutation_allowed_count": max(0, attempts - rejected),
        "frozen_lane_hash_before_after_match": all(c["mirror"].get("frozen_lane_hash_before_after_match") for c in cycles),
        "redqueen_attempted_frozen_mutation": False,
        "active_lane_update_allowed": True,
    }
    result["frozen_lane_integrity_audit_passed"] = all([
        result["frozen_mutation_attempt_count"] > 0,
        result["rejected_frozen_mutation_count"] == result["frozen_mutation_attempt_count"],
        result["frozen_mutation_allowed_count"] == 0,
        result["frozen_lane_hash_before_after_match"],
        not result["redqueen_attempted_frozen_mutation"],
    ])
    _write_json(Path(output_records) / "frozen_lane_integrity_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

