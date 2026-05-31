from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.ironjudge_claim_reconciler import clean_observed, reconcile_claim
from jianmu.self_learning.darwinforge.ironjudge_level_semantics import detect_level_accounting_mode, reconcile_effective_invocations


def build_accounting_reconciliation(source_records_v18: str | Path, source_records_v18_1: str | Path, output_records: str | Path, accounting_mode: str = "auto") -> Dict[str, Any]:
    del source_records_v18
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    v181 = Path(source_records_v18_1)
    scaleup = _read_json(v181 / "ironjudge_resumable_scaleup.json")
    accounting = _read_json(v181 / "ironjudge_invocation_accounting.json")
    readiness = _read_json(v181 / "ironjudge_scaleup_readiness.json")
    mode_info = detect_level_accounting_mode(scaleup)
    selected = mode_info["level_accounting_mode_detected"] if accounting_mode == "auto" else accounting_mode
    effective = reconcile_effective_invocations(scaleup, accounting, selected)
    levels = {row.get("level_name"): row for row in scaleup.get("levels", [])}
    gate = levels.get("gate_5k", {})
    main = levels.get("main_20k", {})
    extended = levels.get("extended_50k", {})
    gate_completed = effective["gate_5k_effective_invocations"] >= 5000
    main_completed = effective["main_20k_effective_invocations"] >= 20000
    extended_completed = effective["extended_50k_effective_invocations"] >= 50000
    gate_clean = gate_completed and clean_observed(gate)
    main_reference = extended if selected == "cumulative" and effective["main_20k_effective_invocations"] >= extended.get("completed_invocations", 0) else main
    main_clean = main_completed and clean_observed(main_reference)
    extended_observed_clean = clean_observed(extended)
    extended_completed_clean = extended_completed and extended_observed_clean
    original_claim = str(readiness.get("recommended_claim_level", "unknown"))
    claim_conflict = original_claim == "ironjudge_20k_clean_frontier_evidence_strengthened" and not bool(readiness.get("main_20k_completed"))
    fields_consistent = not (main_clean and not main_completed)
    claim = reconcile_claim(original_claim, gate_completed, gate_clean, main_completed, main_clean, extended_completed, extended_completed_clean, bool(accounting.get("accounting_passed")), fields_consistent)
    result = {
        "previous_v0_9_18_invocation_count": accounting.get("previous_v0_9_18_invocation_count", 0),
        "v0_9_18_1_new_invocation_count": accounting.get("new_invocation_count", 0),
        "total_accounted_invocation_count": accounting.get("total_accounted_invocation_count", 0),
        **mode_info,
        "level_accounting_mode_selected": selected,
        **effective,
        "gate_5k_completed_reconciled": gate_completed,
        "main_20k_completed_reconciled": main_completed,
        "extended_50k_completed_reconciled": extended_completed,
        "gate_5k_clean_reconciled": gate_clean,
        "main_20k_clean_reconciled": main_clean,
        "extended_50k_clean_reconciled": extended_completed_clean,
        "extended_50k_observed_clean": extended_observed_clean,
        "extended_50k_partial": bool(extended.get("partial")) and not extended_completed,
        "original_claim_level": original_claim,
        "reconciled_claim_level": claim["recommended_claim_level"],
        "claim_conflict_detected": claim_conflict,
        "claim_conflict_resolved": claim_conflict and claim["final_claim_consistent_with_fields"],
        "accounting_passed": bool(accounting.get("accounting_passed")),
        "reconciliation_notes": [
            "v0.9.18.1 level counters form a cumulative chain: v0.9.18 previous -> gate -> main -> extended.",
            "main_20k readiness is therefore judged on cumulative clean observed invocations, not the stale per-row completed flag.",
            "extended_50k remains partial because 27,800 < 50,000.",
        ],
    }
    _write_json(out / "ironjudge_accounting_reconciliation.json", result)
    (out / "ironjudge_accounting_reconciliation.md").write_text(_md(result), encoding="utf-8")
    _write_json(out / "ironjudge_claim_reconciliation.json", claim | {"claim_conflict_detected": claim_conflict, "claim_conflict_resolved": result["claim_conflict_resolved"]})
    return result


def _md(result: Dict[str, Any]) -> str:
    lines = ["# IronJudge Accounting Reconciliation", ""]
    for key in [
        "level_accounting_mode_selected",
        "claim_conflict_detected",
        "claim_conflict_resolved",
        "gate_5k_effective_invocations",
        "main_20k_effective_invocations",
        "extended_50k_effective_invocations",
        "reconciled_claim_level",
    ]:
        lines.append(f"- {key}: {result.get(key)}")
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
