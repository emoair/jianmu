from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from jianmu.self_learning.darwinforge.redqueen_truth_gate_schema import STILL_NOT_PROVEN_MIRROR


def classify_mirror_landing(output_records: str | Path, source: Dict[str, object], repair_applied: bool, runtime_probe: Dict[str, object], negative: Dict[str, object], integration: Dict[str, object]) -> Dict[str, object]:
    preexisting = bool(source.get("mirror_preexisting_landing_found"))
    docs_only = bool(source.get("mirror_docs_only_detected"))
    records_only = bool(source.get("mirror_records_only_detected"))
    partial = source.get("landing_status") == "partial_landing"
    if preexisting and runtime_probe.get("mirror_runtime_probe_passed"):
        landing = "preexisting_landing_confirmed"
    elif partial and repair_applied and runtime_probe.get("mirror_runtime_probe_passed"):
        landing = "partial_landing_repaired"
    elif repair_applied and runtime_probe.get("mirror_runtime_probe_passed"):
        landing = "not_landed_before_repaired_now"
    elif docs_only or records_only:
        landing = "doc_only_not_landed"
    else:
        landing = "blocked"
    result = {
        "mirror_landing_classification_completed": True,
        "preexisting_runtime_landing_found": preexisting,
        "docs_only_claim_detected": docs_only,
        "records_only_claim_detected": records_only,
        "partial_landing_detected": partial,
        "landing_repair_applied": repair_applied,
        "minimal_landing_repair_scope": "state_machine_metrics_redqueen_integration_runtime_trace_negative_boundary",
        "runtime_probe_passed": bool(runtime_probe.get("mirror_runtime_probe_passed")),
        "negative_boundary_passed": bool(negative.get("mirror_negative_boundary_audit_passed")),
        "redqueen_integration_passed": bool(integration.get("mirror_redqueen_integration_passed")),
        "landing_classification": landing,
    }
    _write_json(Path(output_records) / "mirror_landing_classification.json", result)
    return result


def build_mirror_landing_readiness(output_records: str | Path, payload: Dict[str, object]) -> Dict[str, object]:
    blocking = []
    if not payload.get("redqueen_truth_gate_passed"):
        blocking.append("redqueen_truth_gate_failed")
        level = "mirror_landing_blocked_by_redqueen_truth_gate"
    elif payload.get("landing_classification") == "doc_only_not_landed":
        level = "mirror_claim_doc_only_not_landed"
    elif not payload.get("mirror_runtime_probe_passed"):
        blocking.append("runtime_probe_failed")
        level = "mirror_landing_blocked_by_runtime_probe"
    elif not payload.get("mirror_negative_boundary_audit_passed"):
        blocking.append("negative_boundary_failed")
        level = "mirror_landing_blocked_by_negative_boundary"
    elif payload.get("landing_classification") == "preexisting_landing_confirmed":
        level = "mirror_alternating_freeze_landing_confirmed"
    elif payload.get("landing_classification") in {"partial_landing_repaired", "not_landed_before_repaired_now"}:
        level = "mirror_alternating_freeze_landing_repaired"
    else:
        blocking.append("landing_classification_not_positive")
        level = "failed"
    result = {
        **payload,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
        "real_promotion_enabled": False,
        "default_profile_unchanged": True,
        "required_next_run": "Human review of v1.0.8.7 mirror landing evidence before any longer stability rerun or production-profile work.",
        "still_not_proven": list(STILL_NOT_PROVEN_MIRROR),
    }
    _write_json(Path(output_records) / "mirror_landing_readiness.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

