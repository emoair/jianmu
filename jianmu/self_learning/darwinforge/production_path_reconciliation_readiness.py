from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.production_path_reconciliation_schema import base_claim_flags


def build_production_path_reconciliation_readiness(output_records: str | Path, validation: Dict[str, Any], trace_pack: Dict[str, Any], metric: Dict[str, Any], claim: Dict[str, Any], audit_imported: bool = True) -> Dict[str, Any]:
    flags = base_claim_flags()
    bridge_clean = (
        validation.get("compiler_verified_correctness_rate", 0.0) == 1.0
        and validation.get("wrong_stdout", 1) == 0
        and validation.get("timeout", 1) == 0
        and not validation.get("stubbed_validation_detected", True)
        and not validation.get("summary_only_validation_detected", True)
    )
    blocking: List[str] = []
    if not audit_imported:
        blocking.append("audit_report_not_imported")
    if trace_pack.get("blocking_issues"):
        blocking.extend(trace_pack["blocking_issues"])
    if not bridge_clean:
        blocking.append("real_ir_bridge_validation_not_clean")
    if not metric.get("metric_provenance_completed"):
        blocking.append("metric_provenance_incomplete")
    if not claim.get("claim_boundary_fix_completed"):
        blocking.append("claim_boundary_fix_incomplete")
    if bridge_clean and claim.get("claim_boundary_fix_completed") and metric.get("metric_provenance_completed") and trace_pack.get("evidence_trace_pack_generated"):
        level = "real_bridge_positive_but_trace_pack_partial" if trace_pack.get("blocking_issues") else "reconciliation_fixpack_positive"
    elif claim.get("claim_boundary_fix_completed") and metric.get("metric_provenance_completed"):
        level = "evidence_boundary_fixed_but_real_bridge_partial"
    elif trace_pack.get("blocking_issues"):
        level = "blocked_by_raw_trace_missing"
    else:
        level = "failed"
    result = {
        **flags,
        "audit_report_imported": audit_imported,
        "production_runtime_function_support_before": "not_established",
        "production_runtime_array_support_before": "not_established",
        "production_runtime_recursion_support_before": "not_established",
        "atomic_synthesis_non_arithmetic_before": "not_supported",
        "function_ir_added": True,
        "array_ir_added": True,
        "recursive_ir_added": True,
        "extended_emitter_added": True,
        "atomic_synthesis_function_policy_added": True,
        "atomic_synthesis_array_policy_added": True,
        "atomic_synthesis_function_array_policy_added": True,
        "atomic_synthesis_recursion_policy_added": True,
        "arithmetic_regression_clean": validation.get("arithmetic_regression_clean", False),
        "function_ir_compile_success_rate": validation.get("function_ir_compile_success_rate", 0.0),
        "array_ir_compile_success_rate": validation.get("array_ir_compile_success_rate", 0.0),
        "function_array_ir_compile_success_rate": validation.get("function_array_ir_compile_success_rate", 0.0),
        "structured_recursion_ir_compile_success_rate": validation.get("structured_recursion_ir_compile_success_rate", 0.0),
        "mixed_extended_ir_compile_success_rate": validation.get("mixed_extended_ir_compile_success_rate", 0.0),
        "compiler_verified_correctness_rate": validation.get("compiler_verified_correctness_rate", 0.0),
        "raw_trace_available_in_v1_package": trace_pack.get("raw_trace_available_in_v1_package", False),
        "raw_trace_available_in_current_workspace": trace_pack.get("raw_trace_available_in_current_workspace", False),
        "evidence_trace_pack_generated": trace_pack.get("evidence_trace_pack_generated", False),
        "metric_provenance_completed": metric.get("metric_provenance_completed", False),
        "fixed_metric_scaffold_count": metric.get("fixed_metric_scaffold_count", 0),
        "claim_boundary_fix_completed": claim.get("claim_boundary_fix_completed", False),
        "experimental_function_array_recursion_bridge_positive": bridge_clean,
        "ready_for_real_capability_review": bridge_clean and not claim.get("production_function_support_completed", True),
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "Include replayable V1.0 raw trace pack and expand review of experimental bridge before any production promotion.",
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "production_path_reconciliation_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result

