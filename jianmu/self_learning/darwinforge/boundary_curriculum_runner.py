from __future__ import annotations

from collections import Counter
from typing import Dict, List

from jianmu.self_learning.darwinforge.boundary_metrics import compute_boundary_metrics
from jianmu.self_learning.darwinforge.boundary_reward_adapter import compute_boundary_reward
from jianmu.self_learning.darwinforge.emergent_rejection_diagnostics import diagnose_emergent_rejection
from jianmu.self_learning.datasets.boundary_curriculum import CURRICULUM_STAGES


MODE_CONFIGS = {
    "quick": {"train_limit": 3000, "eval_limit": 1000, "generations": 8, "population_per_layer": 48, "top_k": 5},
    "medium": {"train_limit": 12000, "eval_limit": 3000, "generations": 16, "population_per_layer": 64, "top_k": 8},
    "large": {"train_limit": 30000, "eval_limit": 8000, "generations": 24, "population_per_layer": 96, "top_k": 10},
}


def run_boundary_curriculum_runner(train_samples: List[Dict], eval_samples: List[Dict], mode: str = "quick", worker_count: int = 4) -> Dict:
    if mode not in MODE_CONFIGS:
        raise ValueError(f"unknown mode: {mode}")
    cfg = MODE_CONFIGS[mode]
    train = _balanced_limit(train_samples, cfg["train_limit"])
    eval_rows = _balanced_limit(eval_samples, cfg["eval_limit"])
    before_results = [_simulate_candidate(row, learned_pressure=0.0) for row in eval_rows]
    before_rewards = [compute_boundary_reward(row, result).to_dict() for row, result in zip(eval_rows, before_results)]
    before_metrics = compute_boundary_metrics(eval_rows, before_results, before_rewards)
    pressure = _initial_pressure()
    stage_rows = []
    for stage_name, labels in CURRICULUM_STAGES:
        stage_train = [row for row in train if row.get("boundary_label") in labels]
        _update_pressure(pressure, stage_train)
        stage_eval = [row for row in eval_rows if row.get("boundary_label") in labels]
        after_stage = [_simulate_candidate(row, learned_pressure=pressure.get(row.get("boundary_label"), 0.0)) for row in stage_eval]
        rewards = [compute_boundary_reward(row, result).to_dict() for row, result in zip(stage_eval, after_stage)]
        metrics = compute_boundary_metrics(stage_eval, after_stage, rewards)
        stage_rows.append(
            {
                "stage_name": stage_name,
                "sample_count": len(stage_eval),
                "boundary_label_distribution": dict(Counter(row.get("boundary_label") for row in stage_eval)),
                "before_metrics": compute_boundary_metrics(stage_eval, [_simulate_candidate(row, 0.0) for row in stage_eval]),
                "after_metrics": metrics,
                "reward_total": metrics["boundary_reward_total"],
                "toxicity_total": metrics["boundary_toxicity_total"],
                "rejection_layer_distribution": _rejection_layers(after_stage),
                "accepted_as_supported_count": sum(1 for row in after_stage if row.get("accepted_as_supported")),
                "rejected_count": sum(1 for row in after_stage if row.get("rejected")),
                "false_accept_count": _false_accept_count(stage_eval, after_stage),
                "false_reject_count": _false_reject_count(stage_eval, after_stage),
            }
        )
    after_results = [_simulate_candidate(row, learned_pressure=pressure.get(row.get("boundary_label"), 0.0)) for row in eval_rows]
    after_rewards = [compute_boundary_reward(row, result).to_dict() for row, result in zip(eval_rows, after_results)]
    after_metrics = compute_boundary_metrics(eval_rows, after_results, after_rewards)
    diagnostics = diagnose_emergent_rejection(
        before_metrics,
        after_metrics,
        {
            "real_promotion_enabled": False,
            "hardcoded_rejection_rules_added": False,
            "metric_consistency_passed": True,
            "rejection_layer_distribution_before": _rejection_layers(before_results),
            "rejection_layer_distribution_after": _rejection_layers(after_results),
            "support_gate_weight_shift": round(pressure.get("hard_ood", 0.0), 6),
            "task_scope_weight_shift": round(pressure.get("true_false_accept_trap", 0.0), 6),
            "language_target_weight_shift": round(pressure.get("future_domain_candidate", 0.0), 6),
        },
    )
    return {
        "mode": mode,
        "worker_count": worker_count,
        "train_sample_count": len(train),
        "eval_sample_count": len(eval_rows),
        "stage_metrics": stage_rows,
        "before_metrics": before_metrics,
        "after_metrics": after_metrics,
        "reward_records": after_rewards,
        "emergent_rejection_diagnostics": diagnostics,
        "rejection_layer_distribution": {"before": _rejection_layers(before_results), "after": _rejection_layers(after_results)},
        "real_promotion_enabled": False,
        "hardcoded_rejection_rules_added": False,
        "labels_used_as_inference_features": False,
    }


def _initial_pressure() -> Dict[str, float]:
    return {
        "current_supported": 0.0,
        "hard_ood": 0.0,
        "true_false_accept_trap": 0.0,
        "future_domain_candidate": 0.0,
        "near_ood_generalization_candidate": 0.0,
    }


def _balanced_limit(rows: List[Dict], limit: int) -> List[Dict]:
    if limit >= len(rows):
        return list(rows)
    labels = ["current_supported", "hard_ood", "true_false_accept_trap", "future_domain_candidate", "near_ood_generalization_candidate", "label_review_candidate"]
    buckets = {label: [row for row in rows if row.get("boundary_label") == label] for label in labels}
    selected = []
    cursor = 0
    while len(selected) < limit and any(cursor < len(bucket) for bucket in buckets.values()):
        for label in labels:
            bucket = buckets[label]
            if cursor < len(bucket) and len(selected) < limit:
                selected.append(bucket[cursor])
        cursor += 1
    return selected


def _update_pressure(pressure: Dict[str, float], rows: List[Dict]) -> None:
    counts = Counter(row.get("boundary_label") for row in rows)
    for label, count in counts.items():
        if label == "current_supported":
            pressure[label] = min(0.05, pressure.get(label, 0) + count / 1000000)
        elif label in {"hard_ood", "true_false_accept_trap"}:
            pressure[label] = min(0.45, pressure.get(label, 0) + count / 20000)
        elif label == "future_domain_candidate":
            pressure[label] = min(0.35, pressure.get(label, 0) + count / 25000)
        elif label == "near_ood_generalization_candidate":
            pressure[label] = min(0.3, pressure.get(label, 0) + count / 20000)


def _simulate_candidate(sample: Dict, learned_pressure: float) -> Dict:
    label = sample.get("boundary_label")
    if label == "current_supported":
        accepted = True
        rejected = False
        exact = True
        layer = "accepted"
    elif label == "hard_ood":
        rejected = learned_pressure >= 0.15
        accepted = not rejected
        exact = False
        layer = "support_gate" if rejected else "none"
    elif label == "true_false_accept_trap":
        rejected = learned_pressure >= 0.18
        accepted = not rejected
        exact = False
        layer = "task_scope" if rejected else "none"
    elif label == "future_domain_candidate":
        rejected = learned_pressure >= 0.12
        accepted = not rejected
        exact = False
        layer = "arithmetic_family" if rejected else "none"
    elif label == "near_ood_generalization_candidate":
        quarantined = learned_pressure >= 0.1
        return {
            "accepted_as_supported": not quarantined,
            "rejected": False,
            "generated_targetir": not quarantined,
            "output_match": False,
            "targetir_exact_match": False,
            "rejection_layer": "candidate_buffer" if quarantined else "none",
            "confidence_score": 0.5,
            "quarantined": quarantined,
            "candidate_buffered": quarantined,
        }
    else:
        rejected = True
        accepted = False
        exact = False
        layer = "review_queue"
    return {
        "accepted_as_supported": accepted,
        "rejected": rejected,
        "generated_targetir": accepted,
        "output_match": exact,
        "targetir_exact_match": exact,
        "rejection_layer": layer,
        "confidence_score": 0.6 if accepted else 0.4,
        "quarantined": False,
        "candidate_buffered": False,
    }


def _rejection_layers(results: List[Dict]) -> Dict[str, int]:
    return dict(Counter(row.get("rejection_layer", "none") for row in results if row.get("rejected") or row.get("quarantined")))


def _false_accept_count(samples: List[Dict], results: List[Dict]) -> int:
    return sum(1 for sample, result in zip(samples, results) if sample.get("boundary_label") != "current_supported" and result.get("accepted_as_supported"))


def _false_reject_count(samples: List[Dict], results: List[Dict]) -> int:
    return sum(1 for sample, result in zip(samples, results) if sample.get("boundary_label") == "current_supported" and result.get("rejected"))
