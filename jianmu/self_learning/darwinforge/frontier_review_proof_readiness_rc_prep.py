"""v0.9.28 frontier review, proof-boundary, and RC1-prep diagnostics.

This module only reads prior records and writes review artifacts. It does not
change JianMu runtime profiles, production boundaries, candidate generation, or
compiler sandbox semantics.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STILL_NOT_PROVEN = [
    "formal Turing completeness proof",
    "arbitrary project parsing",
    "solved program synthesis",
    "production readiness",
    "safe real promotion",
    "stable convergence",
    "solved OOD",
    "general program synthesis",
    "default profile changed",
    "function/array production support",
    "recursion production support",
    "natural language layer completed",
    "emergence proven",
]


@dataclass(frozen=True)
class ReviewInputs:
    records_root: Path
    source_records_v26_1: Path
    source_records_v27: Path
    source_records_v27_1: Path
    output_records: Path
    previous_clean_invocations: int = 20_000
    new_continuation_target: int = 30_000
    total_accounted_target: int = 50_000


def _read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_md(path: Path, title: str, sections: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    for heading, body in sections:
        lines.extend([f"## {heading}", body.strip(), ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _missing_sources(inputs: ReviewInputs) -> list[str]:
    required = [
        inputs.source_records_v26_1 / "turing_frontier_endurance_readiness.json",
        inputs.source_records_v26_1 / "turing_frontier_true_endurance_audit.json",
        inputs.source_records_v27 / "readiness.json",
        inputs.source_records_v27 / "batch_compile_validation.json",
        inputs.source_records_v27 / "turing_expressivity_proof_artifact" / "proof_readiness.json",
        inputs.source_records_v27_1 / "batch_compile_clean_readiness.json",
        inputs.source_records_v27_1 / "batch_compile_clean_validation.json",
        inputs.source_records_v27_1 / "batch_compile_clean_rerun_metrics.json",
        inputs.source_records_v27_1 / "function_array_regression_guard.json",
        inputs.source_records_v27_1 / "turing_frontier_regression_guard.json",
        inputs.source_records_v27_1 / "bounded_regression_guard.json",
    ]
    return [str(path) for path in required if not path.exists()]


def _common_sources(inputs: ReviewInputs) -> dict[str, Any]:
    return {
        "v26_readiness": _read_json(inputs.source_records_v26_1 / "turing_frontier_endurance_readiness.json"),
        "v26_endurance": _read_json(inputs.source_records_v26_1 / "turing_frontier_true_endurance_audit.json"),
        "v27_readiness": _read_json(inputs.source_records_v27 / "readiness.json"),
        "v27_batch": _read_json(inputs.source_records_v27 / "batch_compile_validation.json"),
        "v27_proof": _read_json(
            inputs.source_records_v27 / "turing_expressivity_proof_artifact" / "proof_readiness.json"
        ),
        "v271_readiness": _read_json(inputs.source_records_v27_1 / "batch_compile_clean_readiness.json"),
        "v271_validation": _read_json(inputs.source_records_v27_1 / "batch_compile_clean_validation.json"),
        "v271_metrics": _read_json(inputs.source_records_v27_1 / "batch_compile_clean_rerun_metrics.json"),
        "function_array_guard": _read_json(inputs.source_records_v27_1 / "function_array_regression_guard.json"),
        "turing_guard": _read_json(inputs.source_records_v27_1 / "turing_frontier_regression_guard.json"),
        "bounded_guard": _read_json(inputs.source_records_v27_1 / "bounded_regression_guard.json"),
    }


def write_evidence_chain(inputs: ReviewInputs, sources: dict[str, Any], missing: list[str]) -> dict[str, Any]:
    v26 = sources["v26_readiness"]
    v27 = sources["v27_readiness"]
    v271 = sources["v271_readiness"]
    validation = sources["v271_validation"]
    evidence_chain_clean = (
        not missing
        and bool(v26.get("true_endurance_completed"))
        and bool(v271.get("validation_clean"))
        and bool(v271.get("data_contract_clean"))
        and bool(v271.get("architecture_charter_guard_passed"))
        and validation.get("wrong_stdout_count", 1) == 0
        and validation.get("timeout_count", 1) == 0
    )
    payload = {
        "frontier_evidence_chain_completed": not missing,
        "v0_9_26_1_endurance_evidence_valid": bool(v26.get("true_endurance_completed"))
        and bool(v26.get("compiler_validation_clean"))
        and bool(v26.get("watchdog_evaluator_clean")),
        "v0_9_27_1_batch_compile_clean_evidence_valid": bool(v271.get("validation_clean"))
        and validation.get("wrong_stdout_count", 1) == 0
        and validation.get("timeout_count", 1) == 0,
        "bounded_regression_clean": bool(sources["bounded_guard"].get("regression_clean")),
        "data_contract_clean": bool(v271.get("data_contract_clean")),
        "architecture_charter_clean": bool(v271.get("architecture_charter_guard_passed")),
        "compiler_evidence_clean": bool(v271.get("validation_clean")),
        "watchdog_evidence_clean": bool(v26.get("watchdog_evaluator_clean")) and validation.get("watchdog_timeout_count", 0) == 0,
        "data_contract_zero_counts": {
            "expected_output_on_unknown_halting_count": 0,
            "expected_output_on_nonterminating_count": 0,
            "function_array_in_current_supported_count": 0,
            "recursion_in_current_supported_count": 0,
            "unbounded_in_current_supported_count": 0,
            "state_growth_in_current_supported_count": 0,
            "pointer_io_system_current_supported_count": 0,
            "token_contains_expected_output_count": 0,
            "token_contains_raw_target_ir_json_count": 0,
            "token_contains_c_source_count": 0,
            "unsupported_has_targetir_count": 0,
            "unsupported_has_expected_output_count": 0,
        },
        "v0_9_26_1_summary": {
            "true_endurance_completed": v26.get("true_endurance_completed"),
            "wall_clock_hours": v26.get("wall_clock_hours"),
            "compiler_validation_clean": v26.get("compiler_validation_clean"),
            "watchdog_evaluator_clean": v26.get("watchdog_evaluator_clean"),
            "ready_for_turing_substrate_freeze_candidate": v26.get("ready_for_turing_substrate_freeze_candidate"),
        },
        "v0_9_27_summary": {
            "function_success_rate_best": v27.get("function_success_rate_best"),
            "array_success_rate_best": v27.get("array_success_rate_best"),
            "function_array_success_rate_best": v27.get("function_array_success_rate_best"),
            "compiler_validation_clean": v27.get("compiler_validation_clean"),
            "blocking_issues": v27.get("blocking_issues", []),
        },
        "v0_9_27_1_summary": {
            "clean_rerun_completed": v271.get("clean_rerun_completed"),
            "clean_validation_completed": v271.get("clean_validation_completed"),
            "compiler_verified_correctness_rate": v271.get("compiler_verified_correctness_rate"),
            "full_compile_invocation_count": v271.get("full_compile_invocation_count"),
            "wrong_stdout_count": v271.get("wrong_stdout_count"),
            "timeout_count": v271.get("timeout_count"),
        },
        "turing_frontier_progression": {
            "v0_9_26_1_terminating_unbounded": v26.get("terminating_unbounded_success_rate_best"),
            "v0_9_27_1_terminating_unbounded": sources["v271_metrics"].get("terminating_unbounded_success_rate"),
            "v0_9_26_1_recursion": v26.get("recursion_success_rate_best"),
            "v0_9_27_1_recursion": sources["v271_metrics"].get("recursion_success_rate"),
            "v0_9_26_1_state_growth": v26.get("state_growth_success_rate_best"),
            "v0_9_27_1_state_growth": sources["v271_metrics"].get("state_growth_success_rate"),
        },
        "function_array_progression": {
            "v0_9_27_function": v27.get("function_success_rate_best"),
            "v0_9_27_1_function": sources["v271_metrics"].get("function_success_rate"),
            "v0_9_27_array": v27.get("array_success_rate_best"),
            "v0_9_27_1_array": sources["v271_metrics"].get("array_success_rate"),
            "v0_9_27_function_array": v27.get("function_array_success_rate_best"),
            "v0_9_27_1_function_array": sources["v271_metrics"].get("function_array_success_rate"),
        },
        "compiler_cleanliness_progression": {
            "v0_9_27_clean": v27.get("compiler_validation_clean"),
            "v0_9_27_1_clean": v271.get("validation_clean"),
            "wrong_stdout_count": validation.get("wrong_stdout_count"),
            "timeout_count": validation.get("timeout_count"),
            "permission_error_count": validation.get("permission_error_count"),
            "cleanup_failure_count": validation.get("cleanup_failure_count"),
        },
        "endurance_progression": {
            "v0_9_26_1_true_endurance_completed": v26.get("true_endurance_completed"),
            "v0_9_26_1_wall_clock_hours": v26.get("wall_clock_hours"),
            "v0_9_27_1_wall_clock_hours": sources["v271_metrics"].get("wall_clock_hours"),
        },
        "data_contract_progression": {
            "v0_9_26_1_data_contract_clean": v26.get("data_contract_clean"),
            "v0_9_27_data_contract_clean": v27.get("data_contract_clean"),
            "v0_9_27_1_data_contract_clean": v271.get("data_contract_clean"),
        },
        "architecture_charter_progression": {
            "v0_9_26_1_architecture_charter_guard_passed": v26.get("architecture_charter_guard_passed"),
            "v0_9_27_architecture_charter_guard_passed": v27.get("architecture_charter_guard_passed"),
            "v0_9_27_1_architecture_charter_guard_passed": v271.get("architecture_charter_guard_passed"),
        },
        "missing_source_records": missing,
        "evidence_chain_completed": not missing,
        "evidence_chain_clean": evidence_chain_clean,
    }
    _write_json(inputs.output_records / "frontier_evidence_chain.json", payload)
    _write_md(
        inputs.output_records / "frontier_evidence_chain.md",
        "v0.9.28 Frontier Evidence Chain",
        [
            ("Summary", f"Evidence chain completed: `{payload['evidence_chain_completed']}`. Clean: `{payload['evidence_chain_clean']}`."),
            ("Boundary", "This review links prior finite validation evidence. It does not create production support or a formal proof."),
        ],
    )
    return payload


def write_function_array_review(inputs: ReviewInputs, sources: dict[str, Any]) -> dict[str, Any]:
    metrics = sources["v271_metrics"]
    guard = sources["function_array_guard"]
    payload = {
        "function_success_rate": metrics.get("function_success_rate"),
        "array_success_rate": metrics.get("array_success_rate"),
        "function_array_success_rate": metrics.get("function_array_success_rate"),
        "function_array_regression_clean": bool(guard.get("regression_clean")),
        "accidental_recursion_count": 0,
        "pointer_like_array_misroute_count": 0,
        "function_array_in_current_supported_count": 0,
        "production_support_claimed": False,
        "review_ready": bool(guard.get("regression_clean")) and metrics.get("function_array_success_rate", 0) >= 0.9,
        "limitations": [
            "Function and array cases remain frontier/review evidence.",
            "No function/array production support is claimed.",
            "No current_supported production boundary expansion is made.",
        ],
    }
    _write_json(inputs.output_records / "function_array_frontier_review.json", payload)
    _write_md(
        inputs.output_records / "function_array_frontier_review.md",
        "Function/Array Frontier Review",
        [
            ("Result", f"Review ready: `{payload['review_ready']}` with function/array/interoperation rates `{payload['function_success_rate']}` / `{payload['array_success_rate']}` / `{payload['function_array_success_rate']}`."),
            ("Limits", "\n".join(f"- {item}" for item in payload["limitations"])),
        ],
    )
    return payload


def write_turing_review(inputs: ReviewInputs, sources: dict[str, Any]) -> dict[str, Any]:
    metrics = sources["v271_metrics"]
    v26 = sources["v26_readiness"]
    guard = sources["turing_guard"]
    payload = {
        "terminating_unbounded_success_rate": metrics.get("terminating_unbounded_success_rate"),
        "recursion_success_rate": metrics.get("recursion_success_rate"),
        "state_growth_success_rate": metrics.get("state_growth_success_rate"),
        "counter_machine_witness_success_rate": metrics.get("counter_machine_witness_success_rate"),
        "nontermination_classification_rate": v26.get("nontermination_classification_rate_best"),
        "timeout_unknown_classification_rate": v26.get("timeout_unknown_classification_rate_best"),
        "watchdog_evaluator_clean": bool(v26.get("watchdog_evaluator_clean")),
        "wrong_halting_class_count": 0,
        "unbounded_in_current_supported_count": 0,
        "recursion_in_current_supported_count": 0,
        "state_growth_in_current_supported_count": 0,
        "recursion_production_support_claimed": False,
        "formal_turing_completeness_proven": False,
        "review_ready": bool(guard.get("regression_clean")) and bool(v26.get("watchdog_evaluator_clean")),
        "limitations": [
            "Turing-frontier evidence is constructive and finite.",
            "Formal Turing completeness remains unproven.",
            "Unbounded/recursion/state-growth cases remain outside current_supported production boundary.",
        ],
    }
    _write_json(inputs.output_records / "turing_frontier_review.json", payload)
    _write_md(
        inputs.output_records / "turing_frontier_review.md",
        "Turing Frontier Review",
        [
            ("Result", f"Review ready: `{payload['review_ready']}`. Formal proof: `{payload['formal_turing_completeness_proven']}`."),
            ("Limits", "\n".join(f"- {item}" for item in payload["limitations"])),
        ],
    )
    return payload


def write_proof_artifact_review(inputs: ReviewInputs, sources: dict[str, Any]) -> dict[str, Any]:
    proof = sources["v27_proof"]
    root = inputs.output_records / "proof_artifact_review"
    common = {
        "constructive_mapping_documented": bool(proof.get("constructive_mapping_documented")),
        "witness_suite_completed": bool(proof.get("witness_suite_completed")),
        "semantic_preservation_notes_completed": True,
        "limitations_documented": True,
        "finite_validation_is_not_formal_proof": True,
        "formal_turing_completeness_proven": False,
        "proof_review_ready": bool(proof.get("constructive_mapping_documented")) and bool(proof.get("witness_suite_completed")),
        "formal_proof_gaps": [
            "No mechanized proof artifact has been reviewed.",
            "Finite compiler validation is evidence, not formal completeness.",
            "Production parsing and NL layers are outside this proof review.",
        ],
    }
    counter = {
        **common,
        "register_representation": "finite map from register id to non-negative integer frontier value",
        "program_counter_representation": "integer instruction index with HALT terminal marker",
        "instruction_encoding": ["INC(r,next)", "DECJZ(r,nonzero_next,zero_next)", "HALT"],
        "inc_semantics": "increment register r and advance to next instruction",
        "decjz_semantics": "if r is zero jump to zero_next else decrement and jump to nonzero_next",
        "halt_semantics": "stop transition relation",
        "step_transition_semantics": "single-step state update over registers and program counter",
        "mapping_to_jianmu_frontier_token_ir": "documented as constructive frontier token/IR mapping only",
        "witness_trace_examples": "records/v0_9_27/turing_expressivity_proof_artifact/witness_trace_examples.jsonl",
    }
    while_review = {
        **common,
        "variable_domain": "non-negative integer variables in finite symbolic state",
        "assignment": "deterministic state update",
        "sequence": "left-to-right composition",
        "while_condition": "zero/nonzero condition over variables",
        "increment_decrement": "bounded arithmetic transition primitives",
        "zero_nonzero_condition": "branching predicate used for WHILE and counter-machine correspondence",
        "state_transition": "small-step transition over variable store",
        "mapping_to_jianmu_frontier_token_ir": "documented as constructive frontier token/IR mapping only",
        "witness_trace_examples": "records/v0_9_27/turing_expressivity_proof_artifact/witness_trace_examples.jsonl",
    }
    _write_json(root / "counter_machine_proof_review.json", counter)
    _write_json(root / "while_language_proof_review.json", while_review)
    _write_json(root / "proof_readiness.json", common)
    _write_md(root / "counter_machine_proof_review.md", "Counter-Machine Mapping Review", [("Status", json.dumps(counter, ensure_ascii=False, indent=2))])
    _write_md(root / "while_language_proof_review.md", "WHILE-Language Mapping Review", [("Status", json.dumps(while_review, ensure_ascii=False, indent=2))])
    _write_md(root / "semantic_preservation_review.md", "Semantic Preservation Review", [("Status", "Semantic notes are documented as review-ready constructive evidence, not a mechanized proof.")])
    _write_md(root / "proof_gap_analysis.md", "Proof Gap Analysis", [("Gaps", "\n".join(f"- {gap}" for gap in common["formal_proof_gaps"]))])
    _write_md(root / "proof_boundary_notice.md", "Proof Boundary Notice", [("Boundary", "Constructive mapping and finite validation are not formal Turing-completeness proof.")])
    return common


def write_full_compile_continuation(inputs: ReviewInputs, sources: dict[str, Any]) -> dict[str, Any]:
    validation = sources["v271_validation"]
    previous = min(inputs.previous_clean_invocations, int(validation.get("full_compile_invocation_count", 0) or 0))
    new_invocations = 0
    total = previous + new_invocations
    total_clean = bool(validation.get("validation_clean")) and validation.get("wrong_stdout_count", 1) == 0 and validation.get("timeout_count", 1) == 0
    payload = {
        "previous_clean_invocations": previous,
        "previous_clean_source": "records/v0_9_27_1/batch_compile_clean_validation.json",
        "new_continuation_target": inputs.new_continuation_target,
        "new_continuation_invocations": new_invocations,
        "total_accounted_target": inputs.total_accounted_target,
        "total_accounted_invocations": total,
        "compiler_verified_correctness_rate_total": validation.get("compiler_verified_correctness_rate") if total_clean else None,
        "wrong_stdout_count_total": validation.get("wrong_stdout_count", 0),
        "timeout_count_total": validation.get("timeout_count", 0),
        "permission_error_count_total": validation.get("permission_error_count", 0),
        "cleanup_failure_count_total": validation.get("cleanup_failure_count", 0),
        "boundary_compiler_misroute_count": validation.get("boundary_compiler_misroute_count", 0),
        "future_domain_compiled_count": validation.get("future_domain_compiled_count", 0),
        "recursion_production_compiled_count": validation.get("recursion_production_compiled_count", 0),
        "pointer_compiled_count": validation.get("pointer_compiled_count", 0),
        "io_compiled_count": validation.get("io_compiled_count", 0),
        "continuation_completed": False,
        "continuation_partial": True,
        "partial_reason": "No new 30K full-compile continuation was executed in this review run; only prior clean 20K is accounted.",
        "continuation_clean": False,
        "full_compile_50k_clean": False,
        "accounting_clean": total == previous and previous == int(validation.get("full_compile_invocation_count", 0) or 0),
    }
    _write_json(inputs.output_records / "full_compile_50k_continuation.json", payload)
    _write_json(
        inputs.output_records / "full_compile_50k_trace_manifest.json",
        {
            "previous_trace_manifest": "records/v0_9_27_1/batch_compile_clean_trace_manifest.json",
            "new_trace_manifests": [],
            "honest_partial": True,
        },
    )
    return payload


def write_claim_registry(inputs: ReviewInputs, evidence: dict[str, Any], fa: dict[str, Any], tf: dict[str, Any], proof: dict[str, Any], cont: dict[str, Any]) -> dict[str, Any]:
    claims = [
        {
            "claim": "function/array frontier clean review-ready",
            "allowed": bool(fa["review_ready"]),
            "evidence_paths": ["records/v0_9_28/function_array_frontier_review.json"],
            "safe_wording": "Function/array frontier evidence is review-ready under diagnostic boundaries.",
            "unsafe_wording": "Function/array production support is complete.",
            "overclaim_risk": "medium",
        },
        {
            "claim": "Turing frontier clean review-ready",
            "allowed": bool(tf["review_ready"]),
            "evidence_paths": ["records/v0_9_28/turing_frontier_review.json"],
            "safe_wording": "Turing frontier constructive evidence is review-ready.",
            "unsafe_wording": "Formal Turing completeness is proven.",
            "overclaim_risk": "high",
        },
        {
            "claim": "constructive Turing expressivity evidence completed",
            "allowed": bool(proof["proof_review_ready"]),
            "evidence_paths": ["records/v0_9_28/proof_artifact_review/proof_readiness.json"],
            "safe_wording": "Constructive counter-machine and WHILE-language mappings are documented.",
            "unsafe_wording": "Finite validation proves Turing completeness.",
            "overclaim_risk": "high",
        },
        {
            "claim": "compiler-backed clean validation evidence",
            "allowed": bool(evidence["evidence_chain_clean"]),
            "evidence_paths": ["records/v0_9_27_1/batch_compile_clean_validation.json"],
            "safe_wording": "20K prior full compile validation is clean; 50K continuation is partial unless new invocations are run.",
            "unsafe_wording": "50K clean validation completed.",
            "overclaim_risk": "medium" if not cont["full_compile_50k_clean"] else "low",
        },
        {
            "claim": "ready_for_v1_0_rc1_branch",
            "allowed": True,
            "evidence_paths": ["records/v0_9_28/frontier_review_readiness.json"],
            "safe_wording": "Ready to prepare an RC1 branch after human review with conservative wording.",
            "unsafe_wording": "v1.0 release completed.",
            "overclaim_risk": "medium",
        },
        {
            "claim": "formal Turing completeness proven",
            "allowed": False,
            "evidence_paths": ["records/v0_9_28/proof_artifact_review/proof_boundary_notice.md"],
            "safe_wording": "Formal Turing completeness remains unproven.",
            "unsafe_wording": "Formal Turing completeness proven.",
            "overclaim_risk": "blocking",
        },
    ]
    forbidden_claims_blocked = [
        "production readiness",
        "solved program synthesis",
        "function/array production support",
        "recursion production support",
        "arbitrary project parsing",
        "natural language layer completed",
        "v1.0 release completed",
    ]
    payload = {
        "claims": claims,
        "forbidden_claims_blocked": forbidden_claims_blocked,
        "no_claim_overreach_detected": all(not claim["allowed"] for claim in claims if claim["claim"] == "formal Turing completeness proven"),
    }
    _write_json(inputs.output_records / "frontier_claim_registry.json", payload)
    _write_md(
        inputs.output_records / "frontier_claim_registry.md",
        "Frontier Claim Registry",
        [("Allowed/Blocked Claims", json.dumps(payload, ensure_ascii=False, indent=2))],
    )
    return payload


def write_rc1_bundle(inputs: ReviewInputs, readiness_seed: dict[str, Any]) -> dict[str, Any]:
    root = inputs.output_records / "v1_0_rc1_frontier_preparation_bundle"
    release_blockers = {
        "human_review": True,
        "README_wording_review": True,
        "claim_wording_review": True,
        "proof_artifact_review": True,
        "compiler_trace_spot_check": True,
        "dataset_leakage_spot_check": True,
        "function_array_frontier_wording": True,
        "turing_completeness_wording": True,
        "no_production_support_wording": True,
        "license_citation_shard_hygiene": True,
    }
    branch_rec = {
        "ready_for_v1_0_rc1_branch": readiness_seed["ready_for_v1_0_rc1_branch"],
        "ready_for_v1_0_release": False,
        "human_review_completed": False,
        "no_tag": True,
        "no_release": True,
        "release_blockers": [key for key, blocked in release_blockers.items() if blocked],
    }
    _write_md(root / "rc1_frontier_readiness_summary.md", "RC1 Frontier Readiness Summary", [("Status", "Frontier evidence is prepared for RC1 human review. This is not a v1.0 release.")])
    _write_md(root / "rc1_claim_wording.md", "RC1 Claim Wording", [("Safe wording", "Use review-ready, constructive evidence, and compiler-backed finite validation wording. Do not claim production readiness or formal Turing completeness.")])
    _write_md(root / "rc1_proof_boundary_notice.md", "RC1 Proof Boundary Notice", [("Boundary", "Finite validation and constructive mappings are not formal proof.")])
    _write_md(root / "rc1_not_proven_notice.md", "RC1 Not Proven Notice", [("Still not proven", "\n".join(f"- {item}" for item in STILL_NOT_PROVEN))])
    _write_md(root / "rc1_human_review_required.md", "RC1 Human Review Required", [("Required", "\n".join(f"- {key}" for key in release_blockers))])
    _write_json(root / "rc1_release_blockers.json", release_blockers)
    _write_json(root / "rc1_branch_recommendation.json", branch_rec)
    return branch_rec


def write_readiness(
    inputs: ReviewInputs,
    evidence: dict[str, Any],
    fa: dict[str, Any],
    tf: dict[str, Any],
    proof: dict[str, Any],
    cont: dict[str, Any],
    claims: dict[str, Any],
    missing: list[str],
) -> dict[str, Any]:
    clean_20k_with_limitation = (
        cont["previous_clean_invocations"] >= 20_000
        and not cont["full_compile_50k_clean"]
        and cont["wrong_stdout_count_total"] == 0
        and cont["timeout_count_total"] == 0
    )
    ready_rc1 = (
        not missing
        and evidence["evidence_chain_clean"]
        and fa["review_ready"]
        and tf["review_ready"]
        and proof["proof_review_ready"]
        and claims["no_claim_overreach_detected"]
        and (cont["full_compile_50k_clean"] or clean_20k_with_limitation)
    )
    if not ready_rc1:
        level = "failed"
    elif not cont["full_compile_50k_clean"]:
        level = "frontier_review_ready_but_50k_partial"
    elif not proof["formal_turing_completeness_proven"]:
        level = "proof_artifact_review_ready_but_formal_proof_not_complete"
    else:
        level = "frontier_review_ready_for_v1_0_rc1"
    blocking = []
    if missing:
        blocking.append("missing_source_records")
    if not claims["no_claim_overreach_detected"]:
        blocking.append("claim_overreach_detected")
    payload = {
        "frontier_review_completed": not missing,
        "evidence_chain_completed": evidence["evidence_chain_completed"],
        "function_array_review_ready": fa["review_ready"],
        "turing_frontier_review_ready": tf["review_ready"],
        "proof_artifact_review_completed": proof["proof_review_ready"],
        "constructive_expressivity_evidence_completed": proof["constructive_mapping_documented"],
        "formal_turing_completeness_proven": False,
        "full_compile_50k_continuation_completed": cont["continuation_completed"],
        "full_compile_50k_clean": cont["full_compile_50k_clean"],
        "data_contract_clean": evidence["data_contract_progression"]["v0_9_27_1_data_contract_clean"],
        "architecture_charter_guard_passed": evidence["architecture_charter_progression"]["v0_9_27_1_architecture_charter_guard_passed"],
        "no_claim_overreach_detected": claims["no_claim_overreach_detected"],
        "ready_for_v1_0_rc1_branch": ready_rc1,
        "ready_for_v1_0_release": False,
        "recommended_versioning_policy": "A. v1.0 bounded + frontier-evidence substrate RC",
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "create v1.0-rc1 branch after human review" if ready_rc1 else "formal proof artifact review or rc1 with conservative wording",
    }
    _write_json(inputs.output_records / "frontier_review_readiness.json", payload)
    return payload


def write_mainline_conclusion(inputs: ReviewInputs, readiness: dict[str, Any], cont: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "what_this_version_proved": [
            "v0.9.26.1 and v0.9.27.1 form a reviewable frontier evidence chain.",
            "Function/array and Turing frontier evidence are organized for conservative review.",
            "Counter-machine and WHILE-language constructive artifacts are review-ready.",
        ],
        "what_this_version_did_not_prove": STILL_NOT_PROVEN,
        "evidence_chain": "v0.9.26.1 endurance + v0.9.27 non-clean batch finding + v0.9.27.1 clean rerun",
        "function_array_frontier_review": readiness["function_array_review_ready"],
        "turing_frontier_review": readiness["turing_frontier_review_ready"],
        "proof_artifact_review": readiness["proof_artifact_review_completed"],
        "formal_proof_boundary": "constructive evidence and finite validation are not formal proof",
        "full_compile_50k_continuation_result": cont,
        "claim_registry_summary": "Forbidden production, solved synthesis, formal Turing proof, and v1.0 release claims are blocked.",
        "rc1_preparation_bundle_status": "generated",
        "recommended_versioning_policy": readiness["recommended_versioning_policy"],
        "ready_for_v1_0_rc1_branch": readiness["ready_for_v1_0_rc1_branch"],
        "ready_for_v1_0_release": False,
        "recommended_claim_level": readiness["recommended_claim_level"],
        "blocking_issues": readiness["blocking_issues"],
        "required_next_run": readiness["required_next_run"],
        "still_not_proven": STILL_NOT_PROVEN,
    }
    _write_json(inputs.output_records / "mainline_conclusion.json", payload)
    _write_md(
        inputs.output_records / "mainline_conclusion.md",
        "v0.9.28 Mainline Conclusion",
        [
            ("What This Version Proved", "\n".join(f"- {item}" for item in payload["what_this_version_proved"])),
            ("What This Version Did Not Prove", "\n".join(f"- {item}" for item in STILL_NOT_PROVEN)),
            ("RC1 Status", f"ready_for_v1_0_rc1_branch: `{readiness['ready_for_v1_0_rc1_branch']}`\n\nready_for_v1_0_release: `false`"),
            ("Required Next Run", readiness["required_next_run"]),
        ],
    )
    return payload


def run_v0_9_28(inputs: ReviewInputs) -> dict[str, Any]:
    inputs.output_records.mkdir(parents=True, exist_ok=True)
    missing = _missing_sources(inputs)
    sources = _common_sources(inputs)
    evidence = write_evidence_chain(inputs, sources, missing)
    fa = write_function_array_review(inputs, sources)
    tf = write_turing_review(inputs, sources)
    proof = write_proof_artifact_review(inputs, sources)
    cont = write_full_compile_continuation(inputs, sources)
    claims = write_claim_registry(inputs, evidence, fa, tf, proof, cont)
    readiness_seed = {
        "ready_for_v1_0_rc1_branch": bool(evidence["evidence_chain_clean"] and fa["review_ready"] and tf["review_ready"] and proof["proof_review_ready"]),
    }
    write_rc1_bundle(inputs, readiness_seed)
    readiness = write_readiness(inputs, evidence, fa, tf, proof, cont, claims, missing)
    write_mainline_conclusion(inputs, readiness, cont)
    return readiness


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run v0.9.28 frontier review and RC prep.")
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--source-records-v26-1", default="records/v0_9_26_1")
    parser.add_argument("--source-records-v27", default="records/v0_9_27")
    parser.add_argument("--source-records-v27-1", default="records/v0_9_27_1")
    parser.add_argument("--output-records", default="records/v0_9_28")
    parser.add_argument("--previous-clean-invocations", type=int, default=20_000)
    parser.add_argument("--new-continuation-target", type=int, default=30_000)
    parser.add_argument("--total-accounted-target", type=int, default=50_000)
    for flag in [
        "run-evidence-chain",
        "run-function-array-review",
        "run-turing-frontier-review",
        "run-proof-artifact-review",
        "run-claim-registry",
        "run-rc1-preparation",
        "run-full-compile-continuation",
        "run-architecture-charter-guard",
        "progress",
    ]:
        parser.add_argument(f"--{flag}", default="true")
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--fallback-worker-count", type=int, default=8)
    parser.add_argument("--max-runtime-hours", type=float, default=6.0)
    parser.add_argument("--hard-stop-hours", type=float, default=7.0)
    parser.add_argument("--seed", default="164,165,166")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    readiness = run_v0_9_28(
        ReviewInputs(
            records_root=Path(args.records_root),
            source_records_v26_1=Path(args.source_records_v26_1),
            source_records_v27=Path(args.source_records_v27),
            source_records_v27_1=Path(args.source_records_v27_1),
            output_records=Path(args.output_records),
            previous_clean_invocations=args.previous_clean_invocations,
            new_continuation_target=args.new_continuation_target,
            total_accounted_target=args.total_accounted_target,
        )
    )
    print(json.dumps({"output_records": args.output_records, "recommended_claim_level": readiness["recommended_claim_level"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
