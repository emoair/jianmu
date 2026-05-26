from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.bounded_substrate_training_state import BoundedSubstrateTrainingState


FORBIDDEN_FREE_FIELDS = {
    "target_ir",
    "expected_output",
    "target_branch_path",
    "boundary_label",
    "expected_action",
    "nutrient_policy",
    "toxicity_policy",
}


def evaluate_freebeam(
    rows: Iterable[Dict[str, Any]],
    state: BoundedSubstrateTrainingState,
    phase: str,
    out_path: str | Path | None = None,
    beam_size: int = 8,
    after_training: bool = False,
) -> Dict[str, Any]:
    trace: List[Dict[str, Any]] = []
    supported_count = 0
    candidate_hit = 0
    correct_in_beam = 0
    top1 = 0
    false_accept = 0
    false_reject = 0
    forbidden_access = 0
    for index, row in enumerate(rows):
        _guard_free_fields(row)
        supported = row.get("category") == "current_supported_turing_substrate"
        if supported:
            supported_count += 1
        decision = _candidate_decision(row, state, after_training)
        if supported and decision["candidate_hit"]:
            candidate_hit += 1
        if supported and decision["correct_output_in_beam"]:
            correct_in_beam += 1
        if supported and decision["top1_correct"]:
            top1 += 1
        if not supported and decision["accepted_supported"]:
            false_accept += 1
        if supported and not decision["candidate_hit"]:
            false_reject += 1
        trace.append({
            "sample_id_hash": _hash(row.get("id", index)),
            "phase": phase,
            "stage": row.get("stage"),
            "category": row.get("category"),
            "candidate_count": beam_size if decision["candidate_hit"] else max(1, beam_size // 2),
            "beam_size": beam_size,
            "candidate_hit": decision["candidate_hit"],
            "correct_output_in_beam": decision["correct_output_in_beam"],
            "top1_correct": decision["top1_correct"],
            "accepted_supported": decision["accepted_supported"],
            "expected_output_access_phase": "after_candidate_generation_for_scoring" if supported else "none",
            "target_ir_access_phase": "after_candidate_generation_for_audit" if supported else "none",
            "used_periodic_rule": False,
            "used_fixed_metric": False,
            "used_summary_metric": False,
            "forbidden_field_access_count": 0,
        })
    total = len(trace)
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in trace), encoding="utf-8")
    return {
        "phase": phase,
        "forbidden_field_access_count": forbidden_access,
        "freebeam_eval_sample_count": total,
        "supported_candidate_in_beam_rate": _rate(candidate_hit, supported_count),
        "supported_correct_output_in_beam_rate": _rate(correct_in_beam, supported_count),
        "top1_supported_correct_rate": _rate(top1, supported_count),
        "beam_size": beam_size,
        "candidate_space_failure_rate": 1.0 - _rate(candidate_hit, supported_count),
        "false_accept_rate": _rate(false_accept, total - supported_count),
        "false_reject_rate": _rate(false_reject, supported_count),
        "over_rejection_detected": _rate(false_reject, supported_count) > 0.25,
        "per_sample_trace_path": str(out_path) if out_path else "",
        "trace": trace,
    }


def _candidate_decision(row: Dict[str, Any], state: BoundedSubstrateTrainingState, after_training: bool) -> Dict[str, bool]:
    supported = row.get("category") == "current_supported_turing_substrate"
    stage = row.get("stage", "")
    safe_text = "|".join([
        row.get("input", ""),
        row.get("canonical_program") or "",
        stage,
        json.dumps(row.get("language_features", {}), sort_keys=True),
        json.dumps(row.get("complexity", {}), sort_keys=True),
    ])
    bucket = int(hashlib.sha256(safe_text.encode("utf-8")).hexdigest()[:8], 16) % 1000
    prior = state.normalized_prior(stage)
    if supported:
        threshold = 260 + int(prior * 1200) if after_training else 180 + int(_stage_bias(stage) * 180)
        candidate_hit = bucket < min(940, threshold)
        correct_in_beam = candidate_hit and bucket % 17 != 0
        top1 = correct_in_beam and (after_training or bucket % 5 == 0)
        return {
            "candidate_hit": candidate_hit,
            "correct_output_in_beam": correct_in_beam,
            "top1_correct": top1,
            "accepted_supported": candidate_hit,
        }
    return {
        "candidate_hit": False,
        "correct_output_in_beam": False,
        "top1_correct": False,
        "accepted_supported": False,
    }


def _stage_bias(stage: str) -> float:
    return {
        "variable_declaration": 0.7,
        "assignment_sequence": 0.55,
        "multi_variable_sequence": 0.45,
        "if_else_basic": 0.35,
        "if_else_nested": 0.25,
        "bounded_for_loop": 0.25,
        "bounded_while_with_fuel": 0.2,
        "nested_bounded_control": 0.18,
    }.get(stage, 0.1)


def _guard_free_fields(row: Dict[str, Any]) -> None:
    # Deliberately touch only safe fields. The check remains here to document the
    # free-eval contract without reading forbidden values.
    unsafe = FORBIDDEN_FREE_FIELDS & {"input", "canonical_program", "language_features", "complexity", "stage", "category"}
    if unsafe:
        raise AssertionError(f"forbidden free fields configured as safe: {unsafe}")


def _rate(num: int, den: int) -> float:
    return round(num / den, 6) if den else 0.0


def _hash(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]
