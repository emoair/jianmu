from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_real_landing_schema import STILL_NOT_PROVEN_REAL_LANDING


def write_endurance_report(output_records: str | Path, readiness: Dict[str, Any]) -> None:
    out = Path(output_records)
    lines = [
        "# v1.0.8.4 RedQueen Real Landing and Endurance Validation",
        "",
        "This version runs RedQueen-controlled staged opt-in validation distribution across three governance cycles.",
        "",
        "It does not train models, update weights, modify the default profile, enable real promotion, release, or claim production support completed.",
        "",
        f"- 6h endurance executed: `{readiness.get('wall_clock_minimum_satisfied')}`",
        f"- cycles completed: `{readiness.get('cycles_completed')}`",
        f"- total events: `{readiness.get('total_events')}`",
        f"- real compiler invocations: `{readiness.get('real_compiler_invocations')}`",
        f"- RedQueen controlled distribution: `{readiness.get('redqueen_controlled_distribution')}`",
        f"- weak category detected: `{readiness.get('weak_category_detected')}`",
        f"- no fake weak category detected: `{readiness.get('no_fake_weak_category_detected')}`",
        f"- adaptive curriculum applied: `{readiness.get('adaptive_curriculum_applied')}`",
        f"- distribution effect audit passed: `{readiness.get('distribution_effect_audit_passed')}`",
        f"- frontier pressure audit passed: `{readiness.get('frontier_pressure_audit_passed')}`",
        f"- lifecycle guard passed: `{readiness.get('endurance_lifecycle_guard_passed')}`",
        f"- governance safety audit passed: `{readiness.get('governance_safety_audit_passed')}`",
        f"- default profile unchanged: `{readiness.get('default_profile_unchanged')}`",
        f"- real promotion enabled: `{readiness.get('real_promotion_enabled')}`",
        f"- production support completed: `false`",
        f"- RedQueen autonomous governance completed: `{readiness.get('redqueen_autonomous_governance_completed')}`",
        f"- recommended claim level: `{readiness.get('recommended_claim_level')}`",
        f"- blocking issues: `{readiness.get('blocking_issues')}`",
        f"- required next run: `{readiness.get('required_next_run')}`",
        "",
        "## Still Not Proven",
        "",
    ]
    lines.extend(f"- {item}" for item in STILL_NOT_PROVEN_REAL_LANDING)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "still_not_proven": list(STILL_NOT_PROVEN_REAL_LANDING)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
