from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from jianmu.self_learning.darwinforge.human_review_pack_schema import STILL_NOT_PROVEN


def build_human_review_pack_readiness(output_records: str | Path, source_found: bool, trace_replayable: bool, interface: Dict[str, object], samples: int, replay: Dict[str, object], alignment: Dict[str, object], bundle: Dict[str, object], precheck: Dict[str, object]) -> Dict[str, object]:
    blocking: List[str] = []
    if not source_found:
        blocking.append("source_trace_pack_missing")
    if not interface.get("interface_landing_review_completed"):
        blocking.append("interface_review_incomplete")
    if samples < 300:
        blocking.append("review_samples_below_target")
    if replay.get("replay_fail_count", 1) != 0:
        blocking.append("replay_failures")
    if not alignment.get("alignment_review_completed"):
        blocking.append("alignment_incomplete")
    if not bundle.get("reviewer_evidence_bundle_generated"):
        blocking.append("bundle_missing")
    bypass = bool(interface.get("template_bypass_detected") or interface.get("marker_ir_direct_compile_detected"))
    if bypass:
        blocking.append("template_or_marker_bypass")
    if not source_found:
        level = "blocked_by_missing_trace_pack"
    elif replay.get("replay_fail_count", 0) > 0:
        level = "review_pack_partial_needs_replay_fix"
    elif blocking:
        level = "human_review_pack_ready_with_minor_notes"
    else:
        level = "human_review_pack_ready"
    result = {
        "source_trace_pack_found": source_found,
        "source_trace_pack_replayable": trace_replayable,
        "interface_landing_review_completed": interface.get("interface_landing_review_completed", False),
        "atomic_policy_interfaces_valid": interface.get("atomic_policy_interfaces_valid", False),
        "builder_interfaces_valid": interface.get("builder_interfaces_valid", False),
        "extended_ir_interfaces_valid": interface.get("extended_ir_interfaces_valid", False),
        "extended_emitter_interfaces_valid": interface.get("extended_emitter_interfaces_valid", False),
        "compiler_interfaces_valid": interface.get("compiler_interfaces_valid", False),
        "template_bypass_detected": interface.get("template_bypass_detected", False),
        "marker_ir_direct_compile_detected": interface.get("marker_ir_direct_compile_detected", False),
        "summary_only_validation_detected": interface.get("summary_only_validation_detected", False),
        "cached_result_used_as_new_detected": interface.get("cached_result_used_as_new_detected", False),
        "review_sample_count": samples,
        "review_samples_generated": samples,
        "replay_validation_completed": replay.get("replay_validation_completed", False),
        "replay_sample_count": replay.get("replay_sample_count", 0),
        "replay_success_rate": replay.get("replay_success_rate", 0.0),
        "replay_fail_count": replay.get("replay_fail_count", 0),
        "replay_stdout_mismatch_count": replay.get("replay_stdout_mismatch_count", 0),
        "replay_source_hash_drift_count": replay.get("replay_source_hash_drift_count", 0),
        "replay_policy_path_drift_count": replay.get("replay_policy_path_drift_count", 0),
        "ir_c_stdout_alignment_completed": alignment.get("alignment_review_completed", False),
        "samples_with_ir_json": alignment.get("samples_with_ir_json", 0),
        "samples_with_emitted_c": alignment.get("samples_with_emitted_c", 0),
        "samples_with_stdout_pair": alignment.get("samples_with_stdout_pair", 0),
        "reviewer_evidence_bundle_generated": bundle.get("reviewer_evidence_bundle_generated", False),
        "artifact_sha256_manifest_generated": bundle.get("artifact_sha256_manifest_generated", False) and alignment.get("artifact_sha256_manifest_generated", False),
        "claim_boundary_review_completed": True,
        "production_dry_run_executed": precheck.get("production_dry_run_executed", False),
        "ready_for_production_dry_run_candidate": precheck.get("ready_for_production_dry_run_candidate", False),
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "ready_for_official_release": False,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "Human review of this bundle, then v1.0.6 production-profile dry-run candidate only if reviewers approve.",
        "workers_requested": replay.get("workers_requested", 1),
        "workers_used": replay.get("workers_used", 1),
        "downgrade_reason": replay.get("downgrade_reason", ""),
        "still_not_proven": list(STILL_NOT_PROVEN),
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "human_review_pack_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result

