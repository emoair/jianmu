from __future__ import annotations

from typing import Dict, Iterable, List

from jianmu.self_learning.darwinforge.reloaded_freebeam_eval import run_reloaded_freebeam_eval


def run_multiseed_boundary_eval(samples: List[Dict], persisted_state: Dict, seeds: Iterable[int], mode: str = "quick", worker_count: int = 4) -> Dict:
    seed_rows = []
    for seed in seeds:
        ordered = _rotate(samples, seed)
        result = run_reloaded_freebeam_eval(ordered, persisted_state, mode=mode, worker_count=worker_count)
        seed_rows.append(
            {
                "seed": seed,
                "current_supported_retention_rate": result["current_supported_retention_rate"],
                "overall_ood_false_accept_rate": result["overall_ood_false_accept_rate"],
                "hard_ood_rejection_rate": result["hard_ood_rejection_rate"],
                "trap_rejection_rate": result["true_false_accept_trap_rejection_rate"],
                "future_domain_isolation_rate": result["future_domain_isolation_rate"],
                "near_ood_quarantine_rate": result["near_ood_quarantine_rate"],
                "no_label_inference_passed": result["no_label_inference_passed"],
                "over_rejection_detected": result["over_rejection_detected"],
            }
        )
    stable = all(
        row["no_label_inference_passed"]
        and row["current_supported_retention_rate"] >= 0.98
        and row["overall_ood_false_accept_rate"] <= 0.05
        and not row["over_rejection_detected"]
        for row in seed_rows
    )
    return {
        "seeds": [row["seed"] for row in seed_rows],
        "seed_metrics": seed_rows,
        "summary": _aggregate(seed_rows),
        "stable_across_seeds": stable,
        "unstable_metric_names": [] if stable else _unstable_metrics(seed_rows),
    }


def _rotate(samples: List[Dict], seed: int) -> List[Dict]:
    if not samples:
        return []
    offset = seed % len(samples)
    return samples[offset:] + samples[:offset]


def _aggregate(rows: List[Dict]) -> Dict:
    numeric_keys = [key for key, value in rows[0].items() if isinstance(value, (int, float)) and key != "seed"] if rows else []
    summary = {}
    for key in numeric_keys:
        vals = [row[key] for row in rows]
        summary[key] = {"mean": round(sum(vals) / len(vals), 6), "min": min(vals), "max": max(vals)}
    return summary


def _unstable_metrics(rows: List[Dict]) -> List[str]:
    unstable = []
    for row in rows:
        if row["current_supported_retention_rate"] < 0.98:
            unstable.append("current_supported_retention_rate")
        if row["overall_ood_false_accept_rate"] > 0.05:
            unstable.append("overall_ood_false_accept_rate")
        if row["over_rejection_detected"]:
            unstable.append("over_rejection_detected")
        if not row["no_label_inference_passed"]:
            unstable.append("no_label_inference_passed")
    return sorted(set(unstable))
