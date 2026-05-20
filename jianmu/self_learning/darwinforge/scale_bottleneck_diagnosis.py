from __future__ import annotations

from typing import Dict, List


def diagnose_scale_bottlenecks(scale_runs: List[Dict]) -> Dict:
    """Classify Colony Scale Stress Probe（根群规模压力探针） bottlenecks."""

    completed = [run for run in scale_runs if not run.get("skipped")]
    if not completed:
        return {
            "scale_limited_likely": False,
            "promotion_limited_likely": False,
            "routing_limited_likely": False,
            "ood_limited_likely": False,
            "resource_limited_likely": False,
            "diagnosis_summary": "No completed scale runs（无已完成规模运行）.",
        }
    first = completed[0]
    last = completed[-1]
    global_gain = _metric(last, "global_correct_targetir_in_beam_rate_after_shadow") - _metric(first, "global_correct_targetir_in_beam_rate_after_shadow")
    stable_gain = _metric(last, "stable_root_count") - _metric(first, "stable_root_count")
    nourished_gain = _metric(last, "nourished_root_count") - _metric(first, "nourished_root_count")
    ood_worse = _metric(last, "ood_false_accept_after_shadow") > _metric(first, "ood_false_accept_after_shadow") + 0.05
    keep_local_many = sum(run.get("keep_local_colony_count", 0) for run in completed) >= sum(run.get("colony_count", 0) for run in completed) * 0.5
    no_shadow_promote = all(run.get("shadow_promote_candidate_count", 0) == 0 for run in completed)
    local_active = any(run.get("stable_root_count", 0) > 0 or run.get("nourished_root_count", 0) > 0 for run in completed)
    global_flat = abs(global_gain) < 0.01
    toxic_high = any(run.get("ood_false_accept_after_shadow", 0.0) >= 0.25 for run in completed) or _toxic_rate(last) > _toxic_rate(first) * 1.5
    resource_limited = any(run.get("total_active_roots", 0) >= run.get("config", {}).get("max_total_active_roots", 10**9) for run in completed)
    resource_limited = resource_limited or _resource_efficiency(last) < _resource_efficiency(first) * 0.5
    scale_limited = (global_gain > 0.02 or stable_gain > 0 or nourished_gain > 0) and not ood_worse
    promotion_limited = keep_local_many and no_shadow_promote and global_flat
    routing_limited = local_active and global_flat
    summary = []
    if scale_limited:
        summary.append("scale_limited（规模受限） signal: larger scale improved local/global metrics without OOD regression.")
    if promotion_limited:
        summary.append("promotion_limited（晋升受限） signal: many keep-local colonies but no shadow promotion candidates.")
    if routing_limited:
        summary.append("routing_limited（路由受限） signal: local colony lifecycle is active while global beam stays flat.")
    if toxic_high:
        summary.append("ood_limited（分布外受限） signal: OOD false accept or toxic nutrient remains high.")
    if resource_limited:
        summary.append("resource_limited（资源受限） signal: active roots hit budget or resource efficiency dropped.")
    if not summary:
        summary.append("No single dominant bottleneck（未出现单一主导瓶颈）.")
    return {
        "scale_limited_likely": scale_limited,
        "promotion_limited_likely": promotion_limited,
        "routing_limited_likely": routing_limited,
        "ood_limited_likely": toxic_high,
        "resource_limited_likely": resource_limited,
        "diagnosis_summary": " ".join(summary),
    }


def compute_cross_scale_metrics(scale_runs: List[Dict]) -> Dict:
    completed = [run for run in scale_runs if not run.get("skipped")]
    return {
        "stable_root_growth_rate_by_scale": _series(completed, "stable_root_count"),
        "nourished_root_growth_rate_by_scale": _series(completed, "nourished_root_count"),
        "ood_toxicity_rate_by_scale": {run["scale_label"]: round(run.get("ood_false_accept_toxic_count", 0) / max(run.get("ood_sample_count", 1), 1), 4) for run in completed},
        "shadow_delta_trend": _series(completed, "shadow_global_delta_avg"),
        "global_beam_trend": _series(completed, "global_correct_targetir_in_beam_rate_after_shadow"),
        "resource_efficiency": {run["scale_label"]: _resource_efficiency(run) for run in completed},
        "runtime_per_100_samples": {run["scale_label"]: round(run.get("runtime_seconds", 0.0) / max((run.get("train_sample_count", 0) + run.get("eval_sample_count", 0) + run.get("ood_sample_count", 0)) / 100.0, 1.0), 4) for run in completed},
    }


def _metric(run: Dict, name: str) -> float:
    return float(run.get(name, 0.0) or 0.0)


def _series(runs: List[Dict], name: str) -> Dict:
    return {run["scale_label"]: run.get(name, 0) for run in runs}


def _toxic_rate(run: Dict) -> float:
    return float(run.get("toxic_event_count", 0)) / max(float(run.get("train_sample_count", 0) + run.get("eval_sample_count", 0) + run.get("ood_sample_count", 0)), 1.0)


def _resource_efficiency(run: Dict) -> float:
    return round(float(run.get("stable_root_count", 0) + run.get("nourished_root_count", 0)) / max(float(run.get("total_active_roots", 0)), 1.0), 4)
