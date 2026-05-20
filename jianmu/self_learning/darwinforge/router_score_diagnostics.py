from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Optional, Tuple

from jianmu.self_learning.branchchain.branch_chain import LAYER_DEFINITIONS
from jianmu.self_learning.branchchain.branch_types import BranchDecision


LOW_SCORE_RANK_CUTOFF = 3


def score_target_branch_path(
    population,
    features: Dict,
    target_branch_path: List[List[str]],
    proposals_per_layer: int = 6,
) -> Dict:
    """Teacher-Guided Diagnostic（教师引导诊断） scorer for target BranchPath（分支路径） options.

    This function is intentionally offline: it scores the teacher path after the
    sample is known, and must not be called by free candidate generation.
    """

    target_pairs = _normalized_target_pairs(target_branch_path)
    target_by_layer = {layer: option for layer, option in target_pairs}
    previous_decisions: List[BranchDecision] = []
    rows = []
    first_low = None
    first_pruned = None
    for layer_name, options in LAYER_DEFINITIONS:
        if layer_name not in target_by_layer:
            continue
        option_scores = _score_options(population, features, previous_decisions, layer_name, options)
        ranked = sorted(option_scores.values(), key=lambda row: (row["score"], row["option"]), reverse=True)
        for rank, row in enumerate(ranked, start=1):
            row["rank"] = rank
        target_option = target_by_layer[layer_name]
        target_row = next((row for row in ranked if row["option"] == target_option), None)
        best = ranked[0] if ranked else {"option": None, "score": 0}
        target_rank = target_row["rank"] if target_row else None
        target_score = target_row["score"] if target_row else 0
        proposed = bool(target_row and target_score >= target_row.get("threshold", 1))
        pruned = bool(target_rank is None or target_rank > proposals_per_layer)
        score_gap = best["score"] - target_score
        row = {
            "layer_name": layer_name,
            "target_option": target_option,
            "target_option_score": target_score,
            "target_option_rank": target_rank,
            "target_option_was_proposed": proposed,
            "target_option_pruned_by_global_beam": pruned,
            "best_option": best["option"],
            "best_option_score": best["score"],
            "score_gap_to_best": score_gap,
            "candidates_count": len(ranked),
            "top_candidates": [
                {"option": item["option"], "score": item["score"], "rank": item["rank"]}
                for item in ranked[: min(len(ranked), 5)]
            ],
        }
        rows.append(row)
        if first_low is None and target_rank is not None and target_rank > LOW_SCORE_RANK_CUTOFF:
            first_low = layer_name
        if first_pruned is None and pruned:
            first_pruned = layer_name
        previous_decisions.append(
            BranchDecision(
                layer_name=layer_name,
                candidates=list(options),
                selected=target_option,
                confidence=int(target_score),
                neuron_id=f"diagnostic:{layer_name}:{target_option}",
                evidence={"teacher_guided_diagnostic": True},
            )
        )
    return {
        "layers": rows,
        "first_low_score_correct_layer": first_low,
        "first_pruned_correct_layer": first_pruned,
        "correct_option_rank_by_layer": {row["layer_name"]: row["target_option_rank"] for row in rows},
        "correct_option_score_by_layer": {row["layer_name"]: row["target_option_score"] for row in rows},
        "proposals_per_layer": proposals_per_layer,
    }


def find_fork_point(score_diag: Dict, free_path_diag: Optional[Dict] = None) -> Dict:
    """Find RootFork（根叉） fork point from score diagnostics and free path diagnostics."""

    free_path_diag = free_path_diag or {}
    rows = list(score_diag.get("layers", []))
    by_layer = {row["layer_name"]: row for row in rows}
    target_order = [row["layer_name"] for row in rows]
    chosen_layer = None
    reason = None
    priority = [
        ("first_pruned_correct_layer", "first_pruned_correct_layer"),
        ("first_low_score_correct_layer", "first_low_score_correct_layer"),
    ]
    for key, label in priority:
        if score_diag.get(key):
            chosen_layer = score_diag[key]
            reason = label
            break
    if chosen_layer is None and free_path_diag.get("first_wrong_layer"):
        chosen_layer = free_path_diag["first_wrong_layer"]
        reason = "first_divergence_layer"
    if chosen_layer is None and free_path_diag.get("first_confidence_collapse_layer"):
        chosen_layer = free_path_diag["first_confidence_collapse_layer"]
        reason = "first_confidence_collapse_layer"
    if chosen_layer is None:
        chosen_layer = "arithmetic_family" if "arithmetic_family" in by_layer else (target_order[0] if target_order else None)
        reason = "fallback_arithmetic_family"
    stable_prefix = []
    for row in rows:
        if row["layer_name"] == chosen_layer:
            break
        stable_prefix.append([row["layer_name"], row["target_option"]])
    selected_row = by_layer.get(chosen_layer, {})
    return {
        "fork_layer": chosen_layer,
        "fork_reason": reason,
        "stable_prefix": stable_prefix,
        "correct_option_at_fork": selected_row.get("target_option"),
        "score_gap": selected_row.get("score_gap_to_best", 0),
        "target_option_rank": selected_row.get("target_option_rank"),
    }


def summarize_router_score_diagnostics(rows: Iterable[Dict]) -> Dict:
    rank_totals = defaultdict(list)
    score_totals = defaultdict(list)
    first_low = Counter()
    first_pruned = Counter()
    forks = Counter()
    for row in rows:
        score_diag = row.get("score_diagnostic", row)
        for layer, rank in score_diag.get("correct_option_rank_by_layer", {}).items():
            if rank is not None:
                rank_totals[layer].append(rank)
        for layer, score in score_diag.get("correct_option_score_by_layer", {}).items():
            score_totals[layer].append(score)
        if score_diag.get("first_low_score_correct_layer"):
            first_low[score_diag["first_low_score_correct_layer"]] += 1
        if score_diag.get("first_pruned_correct_layer"):
            first_pruned[score_diag["first_pruned_correct_layer"]] += 1
        fork = row.get("fork_point", {})
        if fork.get("fork_layer"):
            forks[fork["fork_layer"]] += 1
    return {
        "correct_option_rank_by_layer_summary": {
            layer: round(sum(values) / len(values), 4) for layer, values in sorted(rank_totals.items())
        },
        "correct_option_score_by_layer_summary": {
            layer: round(sum(values) / len(values), 4) for layer, values in sorted(score_totals.items())
        },
        "first_low_score_correct_layer_distribution": dict(first_low),
        "first_pruned_correct_layer_distribution": dict(first_pruned),
        "fork_layer_distribution": dict(forks),
    }


def _score_options(population, features, previous_decisions, layer_name: str, options: List[str]) -> Dict[str, Dict]:
    option_scores = {option: {"option": option, "score": 0, "threshold": 1} for option in options}
    for neuron in population.per_layer.get(layer_name, []):
        if neuron.option not in options:
            continue
        score = neuron.score(features, previous_decisions)
        adjusted = score + int(max(min(neuron.score_value, 20), -20))
        current = option_scores[neuron.option]
        if adjusted >= current["score"]:
            current.update(
                {
                    "score": adjusted,
                    "raw_score": score,
                    "threshold": neuron.threshold,
                    "neuron_id": neuron.neuron_id,
                }
            )
    return option_scores


def _normalized_target_pairs(target_branch_path: List[List[str]]) -> List[Tuple[str, str]]:
    pairs = [tuple(item) for item in target_branch_path]
    layers = {layer for layer, _ in pairs}
    if "support_gate" not in layers and any(layer == "semantic_domain" for layer, _ in pairs):
        insert_at = next((index + 1 for index, (layer, _) in enumerate(pairs) if layer == "semantic_domain"), len(pairs))
        pairs = pairs[:insert_at] + [("support_gate", "supported")] + pairs[insert_at:]
    return pairs
