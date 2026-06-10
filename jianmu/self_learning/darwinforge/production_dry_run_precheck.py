from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


def write_production_dry_run_precheck(output_records: str | Path, review_ready: bool) -> Dict[str, object]:
    result = {
        "production_dry_run_executed": False,
        "ready_for_production_dry_run_candidate": bool(review_ready),
        "production_ready": False,
        "required_before_dry_run": ["human review signoff", "production profile integration design", "rollback plan", "claim boundary approval"],
        "blockers_before_dry_run": [] if review_ready else ["human_review_pack_not_ready"],
        "required_human_review_items": ["policy path", "ExtendedIR", "ExtendedEmitterC", "cl.exe invocation", "stdout match", "trace replay", "no template bypass", "no production overclaim"],
        "suggested_next_branch": "v1.0.6-production-profile-dry-run-candidate",
    }
    Path(output_records).mkdir(parents=True, exist_ok=True)
    (Path(output_records) / "production_dry_run_precheck.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result

