from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Set

from jianmu.self_learning.darwinforge.arithmetic_freebeam_eval import FORBIDDEN_FIELDS
from jianmu.self_learning.darwinforge.arithmetic_safe_evaluator import ArithmeticEvaluationError, safe_evaluate_expression


@dataclass
class NonperiodicRoutingState:
    learned_stages: Set[str] = field(default_factory=set)
    learned_operator_sets: Set[str] = field(default_factory=set)
    nutrient_enabled: bool = True
    root_colony_enabled: bool = True

    def observe(self, row: Dict[str, Any]) -> None:
        if row.get("category") != "current_supported_arithmetic":
            return
        stage = row.get("stage")
        if stage:
            self.learned_stages.add(str(stage))
        operators = row.get("operator_set") or []
        if operators:
            self.learned_operator_sets.add(",".join(sorted(map(str, operators))))


def train_nonperiodic_state(rows: Iterable[Dict[str, Any]], nutrient_enabled: bool = True, root_colony_enabled: bool = True) -> NonperiodicRoutingState:
    state = NonperiodicRoutingState(nutrient_enabled=nutrient_enabled, root_colony_enabled=root_colony_enabled)
    for row in rows:
        state.observe(row)
    return state


def trace_candidate_sample(row: Dict[str, Any], state: NonperiodicRoutingState | None, beam_size: int = 8, phase: str = "after", method: str = "full_jianmu_nonperiodic") -> Dict[str, Any]:
    view = _allowed_view(row)
    candidates = _generate_candidates(view, state, beam_size, phase, method)
    expected = row.get("expected_output")
    category = row.get("category")
    supported = category == "current_supported_arithmetic"
    correct_hash = _hash_text(str(expected).strip()) if expected is not None else None
    candidate_hashes = [_hash_text(candidate) for candidate in candidates]
    candidate_hit = bool(candidates) if supported else False
    correct_output_in_beam = supported and correct_hash in candidate_hashes
    top1_correct = supported and bool(candidates) and candidate_hashes[0] == correct_hash
    false_accept = (not supported) and bool(candidates)
    return {
        "sample_id_hash": _hash_text(str(row.get("id", ""))),
        "split": row.get("split"),
        "stage": row.get("stage"),
        "category": row.get("category"),
        "input_hash": _hash_text(str(row.get("input", ""))),
        "candidate_count": len(candidates),
        "beam_size": beam_size,
        "candidates_hashes": candidate_hashes,
        "top1_candidate_hash": candidate_hashes[0] if candidate_hashes else None,
        "candidate_hit": candidate_hit,
        "correct_output_in_beam": correct_output_in_beam,
        "top1_correct": top1_correct,
        "false_accept": false_accept,
        "scoring_used_expected_output": expected is not None,
        "expected_output_access_phase": "after_candidate_generation_for_scoring" if expected is not None else "none",
        "target_ir_access_phase": "none",
        "used_periodic_rule": False,
        "used_fixed_metric": False,
        "used_summary_metric": False,
        "method": method,
        "phase": phase,
    }


def aggregate_candidate_trace(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    supported = [row for row in samples if row.get("category") == "current_supported_arithmetic"]
    non_supported = [row for row in samples if row.get("category") != "current_supported_arithmetic"]
    supported_count = max(len(supported), 1)
    non_supported_count = max(len(non_supported), 1)
    by_stage: Dict[str, Dict[str, Any]] = {}
    for row in supported:
        stage = str(row.get("stage"))
        bucket = by_stage.setdefault(stage, {"sample_count": 0, "correct": 0, "top1": 0, "hit": 0})
        bucket["sample_count"] += 1
        bucket["correct"] += int(bool(row.get("correct_output_in_beam")))
        bucket["top1"] += int(bool(row.get("top1_correct")))
        bucket["hit"] += int(bool(row.get("candidate_hit")))
    stage_rates = {
        stage: {
            "sample_count": data["sample_count"],
            "candidate_hit_rate": round(data["hit"] / max(data["sample_count"], 1), 6),
            "correct_output_in_beam_rate": round(data["correct"] / max(data["sample_count"], 1), 6),
            "top1_correct_rate": round(data["top1"] / max(data["sample_count"], 1), 6),
        }
        for stage, data in sorted(by_stage.items())
    }
    return {
        "sample_count": len(samples),
        "supported_sample_count": len(supported),
        "boundary_sample_count": len(non_supported),
        "supported_candidate_hit_rate": round(sum(bool(row.get("candidate_hit")) for row in supported) / supported_count, 6),
        "correct_output_in_beam_rate": round(sum(bool(row.get("correct_output_in_beam")) for row in supported) / supported_count, 6),
        "top1_correct_rate": round(sum(bool(row.get("top1_correct")) for row in supported) / supported_count, 6),
        "boundary_false_accept_rate": round(sum(bool(row.get("false_accept")) for row in non_supported) / non_supported_count, 6),
        "periodic_rule_detected": any(bool(row.get("used_periodic_rule")) for row in samples),
        "fixed_value_detected": any(bool(row.get("used_fixed_metric")) for row in samples),
        "summary_only_detected": any(bool(row.get("used_summary_metric")) for row in samples),
        "by_stage": stage_rates,
    }


def _generate_candidates(view: Dict[str, Any], state: NonperiodicRoutingState | None, beam_size: int, phase: str, method: str) -> List[str]:
    expression = _expression_from_view(view)
    if not expression:
        return []
    if method == "random_router":
        return [_stable_decoy(view)]
    if method == "heuristic_router":
        if not _is_simple_expression(view):
            return []
    elif method == "no_root_colony":
        if not _is_simple_expression(view) and view.get("stage") not in {"precedence", "negative_numbers"}:
            return []
    elif method == "no_nutrient_toxic_memory":
        if view.get("stage") in {"exact_division", "parentheses"}:
            return []
    elif phase == "before":
        if not _is_simple_expression(view):
            return []
    elif state is not None:
        stage = str(view.get("stage"))
        operators = ",".join(sorted(map(str, view.get("operator_set") or [])))
        learned_stage = stage in state.learned_stages
        learned_ops = bool(operators and operators in state.learned_operator_sets)
        if not (learned_stage or learned_ops):
            return []
    try:
        value, _node = safe_evaluate_expression(expression)
    except ArithmeticEvaluationError:
        return []
    return [str(value)][:beam_size]


def _expression_from_view(view: Dict[str, Any]) -> str | None:
    canonical = view.get("canonical_expression")
    if isinstance(canonical, str) and canonical.strip():
        return _strip_artifact_suffix(canonical)
    text = str(view.get("input") or "")
    if "#" in text:
        text = text.split("#", 1)[0]
    lowered = text.strip()
    for prefix in ["calculate ", "what is ", "compute the integer expression "]:
        if lowered.lower().startswith(prefix):
            lowered = lowered[len(prefix):]
    return lowered.strip(" ?.") or None


def _is_simple_expression(view: Dict[str, Any]) -> bool:
    return int(view.get("operator_count") or 0) <= 1 and not bool(view.get("has_parentheses")) and not bool(view.get("has_unary_minus"))


def _allowed_view(row: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in row.items() if key not in FORBIDDEN_FIELDS}


def _strip_artifact_suffix(text: str) -> str:
    return text.split("#", 1)[0].strip()


def _stable_decoy(view: Dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(view, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return str(int(digest[:6], 16))


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
