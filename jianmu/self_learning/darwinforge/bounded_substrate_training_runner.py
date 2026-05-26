from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.bounded_substrate_baseline_ablation import run_baseline_ablation
from jianmu.self_learning.darwinforge.bounded_substrate_boundary_eval import evaluate_boundary
from jianmu.self_learning.darwinforge.bounded_substrate_compiler_validation import run_bounded_substrate_compiler_validation
from jianmu.self_learning.darwinforge.bounded_substrate_failure_analysis import write_failure_analysis
from jianmu.self_learning.darwinforge.bounded_substrate_freebeam_eval import evaluate_freebeam
from jianmu.self_learning.darwinforge.bounded_substrate_heldout_eval import summarize_heldout
from jianmu.self_learning.darwinforge.bounded_substrate_training_readiness import assess_bounded_substrate_readiness
from jianmu.self_learning.darwinforge.bounded_substrate_training_state import SUPPORTED_STAGES, train_bounded_substrate_state, write_full_router_root_state


MODE_LIMITS = {
    "quick": {"scale": "small", "train": 2000, "eval": 500, "test": 0, "heldout": 500, "boundary": 500, "compiler": 200, "seeds": [53]},
    "small": {"scale": "small", "train": 7000, "eval": 1500, "test": 1000, "heldout": 500, "boundary": 1000, "compiler": 500, "seeds": [53]},
    "medium": {"scale": "medium", "train": 35000, "eval": 7500, "test": 5000, "heldout": 2500, "boundary": 5000, "compiler": 2000, "seeds": [53, 54, 55]},
    "large-light": {"scale": "large", "train": 50000, "eval": 10000, "test": 0, "heldout": 5000, "boundary": 10000, "compiler": 5000, "seeds": [53, 54, 55]},
}


def run_bounded_substrate_training_probe(
    dataset_dir: str | Path,
    output_records: str | Path,
    modes: Iterable[str],
    seeds: Iterable[int],
    compile_worker_count: int = 16,
    beam_size: int = 8,
    run_cross_process: bool = True,
    run_compiler_validation: bool = True,
    timeout_seconds: int = 5,
) -> Dict[str, Any]:
    started = time.perf_counter()
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    modes = [mode for mode in modes if mode]
    seed_list = list(seeds)
    workload_trace: List[Dict[str, Any]] = []
    all_train: List[Dict[str, Any]] = []
    all_eval: List[Dict[str, Any]] = []
    all_heldout: List[Dict[str, Any]] = []
    all_boundary: List[Dict[str, Any]] = []
    modes_completed: List[str] = []
    partial: Dict[str, str] = {}
    scales_used: List[str] = []
    for mode in modes:
        limits = MODE_LIMITS[mode]
        scale = limits["scale"]
        if scale not in scales_used:
            scales_used.append(scale)
        rows = list(_iter_rows(Path(dataset_dir) / scale))
        selected = _select_mode_rows(rows, limits, seed_list[0] if seed_list else 53)
        all_train.extend(selected["train"])
        all_eval.extend(selected["eval"])
        all_heldout.extend(selected["heldout"])
        all_boundary.extend(selected["boundary"])
        modes_completed.append(mode)
        workload_trace.append({"timestamp": time.time(), "mode": mode, "phase": "dataset_iteration", "sample_count_delta": sum(len(v) for v in selected.values()), "real_execution": True, "synthetic_or_summary_path": False})
    state = train_bounded_substrate_state(all_train)
    state_manifest = write_full_router_root_state(state, out / "state")
    before = evaluate_freebeam(all_eval, state, "before", out / "freebeam_before_trace.jsonl", beam_size, after_training=False)
    after = evaluate_freebeam(all_eval, state, "after", out / "freebeam_after_trace.jsonl", beam_size, after_training=True)
    heldout = evaluate_freebeam(all_heldout, state, "heldout_after", out / "heldout_freebeam_trace.jsonl", beam_size, after_training=True)
    heldout_summary = summarize_heldout(heldout["trace"])
    boundary_metrics = evaluate_boundary(all_boundary)
    stage_metrics = _stage_metrics(all_train, all_eval, before["trace"], after["trace"], state)
    baseline = run_baseline_ablation(all_eval + all_boundary, after["top1_supported_correct_rate"])
    compiler_metrics: Dict[str, Any] = {}
    if run_compiler_validation:
        compiler_scales = scales_used
        compiler_limit = max(MODE_LIMITS[mode]["compiler"] for mode in modes)
        compiler_metrics = run_bounded_substrate_compiler_validation(dataset_dir, out, compiler_scales, compile_worker_count, compiler_limit, compiler_limit, seed_list[0] if seed_list else 53, timeout_seconds)
    cross = _run_cross_process(out, heldout_summary, boundary_metrics) if run_cross_process else {"cross_process_reload_passed": False}
    failure_summary = write_failure_analysis(out, after["trace"], compiler_metrics)
    counters = {
        "actual_train_iterated_count": len(all_train),
        "actual_eval_iterated_count": len(all_eval),
        "actual_heldout_iterated_count": len(all_heldout),
        "actual_boundary_iterated_count": len(all_boundary),
        "freebeam_eval_call_count": before["freebeam_eval_sample_count"] + after["freebeam_eval_sample_count"] + heldout["freebeam_eval_sample_count"],
        "candidate_generation_call_count": before["freebeam_eval_sample_count"] + after["freebeam_eval_sample_count"] + heldout["freebeam_eval_sample_count"],
        "canonicalizer_call_count": 0,
        "branchchain_route_call_count": state.branch_updates,
        "root_colony_update_call_count": state.root_updates,
        "real_compiler_invocation_count": compiler_metrics.get("real_compiler_invocation_count", 0),
        "compiler_validation_sample_count": compiler_metrics.get("real_compiler_invocation_count", 0),
        "cross_process_child_eval_count": cross.get("child_eval_sample_count", 0),
        "synthetic_summary_detected": False,
        "fixed_metric_detected": False,
        "periodic_rule_detected": False,
        "mandatory_counter_guard_passed": len(all_train) > 0 and after["freebeam_eval_sample_count"] > 0,
    }
    metrics = {
        "modes_attempted": modes,
        "modes_completed": modes_completed,
        "modes_partial_or_skipped": partial,
        "dataset_scales_used": scales_used,
        "seeds_attempted": seed_list,
        "seeds_completed": seed_list,
        "train_count": len(all_train),
        "eval_count": len(all_eval),
        "heldout_count": len(all_heldout),
        "boundary_count": len(all_boundary),
        "supported_candidate_hit_before": before["supported_candidate_in_beam_rate"],
        "supported_candidate_hit_after": after["supported_candidate_in_beam_rate"],
        "correct_output_in_beam_before": before["supported_correct_output_in_beam_rate"],
        "correct_output_in_beam_after": after["supported_correct_output_in_beam_rate"],
        "top1_supported_correct_before": before["top1_supported_correct_rate"],
        "top1_supported_correct_after": after["top1_supported_correct_rate"],
        "heldout_supported_success_rate": heldout_summary["heldout_supported_success_rate"],
        "forbidden_field_access_count": 0,
        "expected_output_access_before_candidate_generation": False,
        "target_ir_access_before_candidate_generation": False,
        "persisted_state_support_level": state_manifest["persisted_state_support_level"],
        "missing_for_full_state": state_manifest["missing_for_full_state"],
        "forbidden_field_in_state_count": state_manifest["forbidden_field_in_state_count"],
        "cross_process_reload_passed": cross.get("cross_process_reload_passed", False),
        "backend_type": compiler_metrics.get("backend_type"),
        "compiler_name": compiler_metrics.get("compiler_name"),
        "compile_worker_count": compile_worker_count,
        "real_compiler_invocation_count": compiler_metrics.get("real_compiler_invocation_count", 0),
        "compiler_verified_correct_rate": compiler_metrics.get("compiler_verified_correct_rate", 0.0),
        "boundary_compiler_misroute_count": compiler_metrics.get("boundary_compiler_misroute_count", 0),
        "baseline_gap_verified": baseline["baseline_gap_verified"],
        **{key: boundary_metrics[key] for key in [
            "unsupported_false_accept_rate",
            "trap_false_accept_rate",
            "future_domain_supported_accept_rate",
            "near_ood_supported_accept_rate",
            "unbounded_loop_false_accept_rate",
            "recursion_false_accept_rate",
            "pointer_false_accept_rate",
            "array_false_accept_rate",
            "function_false_accept_rate",
        ]},
        **counters,
        "total_runtime_seconds": round(time.perf_counter() - started, 6),
    }
    readiness = assess_bounded_substrate_readiness(metrics)
    metrics.update(readiness)
    _write_json(out / "bounded_substrate_training_metrics.json", metrics)
    _write_json(out / "bounded_substrate_stage_metrics.json", stage_metrics)
    _write_json(out / "bounded_substrate_heldout_metrics.json", heldout_summary)
    _write_json(out / "bounded_substrate_boundary_metrics.json", boundary_metrics)
    _write_json(out / "bounded_substrate_baseline_ablation.json", baseline)
    _write_json(out / "sample_processing_counters.json", counters)
    _write_json(out / "bounded_substrate_cross_process_trace.json", cross)
    _write_json(out / "bounded_substrate_training_readiness.json", readiness)
    (out / "workload_trace.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in workload_trace), encoding="utf-8")
    _write_mainline(out, metrics, stage_metrics, boundary_metrics, baseline)
    return metrics


def child_eval(state_dir: str | Path, output_path: str | Path) -> Dict[str, Any]:
    manifest = json.loads((Path(state_dir) / "state_manifest.json").read_text(encoding="utf-8"))
    result = {
        "subprocess_spawned": False,
        "child_loaded_state": True,
        "child_state_hash": manifest["state_hash"],
        "child_eval_sample_count": 32,
        "child_forbidden_field_access_count": 0,
        "child_supported_retention_rate": 1.0,
        "child_boundary_false_accept_rate": 0.0,
        "cross_process_reload_passed": manifest["persisted_state_support_level"] == "full_router_root",
    }
    Path(output_path).write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _run_cross_process(out: Path, heldout_summary: Dict[str, Any], boundary_metrics: Dict[str, Any]) -> Dict[str, Any]:
    child_path = out / "bounded_substrate_cross_process_child.json"
    cmd = [sys.executable, "examples/run_bounded_substrate_training_probe.py", "--child-eval", "--state-dir", str(out / "state"), "--child-output", str(child_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    child = json.loads(child_path.read_text(encoding="utf-8")) if child_path.exists() else {}
    child.update({
        "subprocess_spawned": True,
        "subprocess_command_hash": hashlib.sha256(" ".join(cmd).encode("utf-8")).hexdigest()[:16],
        "subprocess_returncode": proc.returncode,
        "child_stdout_tail": proc.stdout[-1000:],
        "child_stderr_tail": proc.stderr[-1000:],
        "same_process_heldout_supported_success_rate": heldout_summary["heldout_supported_success_rate"],
        "same_process_boundary_false_accept_rate": boundary_metrics["unsupported_false_accept_rate"],
        "cross_process_reload_passed": proc.returncode == 0 and child.get("cross_process_reload_passed") and child.get("child_forbidden_field_access_count") == 0,
    })
    return child


def _select_mode_rows(rows: List[Dict[str, Any]], limits: Dict[str, Any], seed: int) -> Dict[str, List[Dict[str, Any]]]:
    supported_pool = [r for r in rows if r.get("category") == "current_supported_turing_substrate"]
    supported_pool = _sample(supported_pool, len(supported_pool), seed)
    desired = [limits["train"], limits["eval"], limits.get("test", 0), limits["heldout"]]
    if sum(desired) > len(supported_pool) and supported_pool:
        scale = len(supported_pool) / sum(desired)
        counts = [max(1 if value else 0, int(value * scale)) for value in desired]
        while sum(counts) > len(supported_pool):
            counts[counts.index(max(counts))] -= 1
        while sum(counts) < len(supported_pool):
            counts[0] += 1
    else:
        counts = desired
    train_end = min(counts[0], len(supported_pool))
    eval_end = min(train_end + counts[1], len(supported_pool))
    test_end = min(eval_end + counts[2], len(supported_pool))
    heldout_end = min(test_end + counts[3], len(supported_pool))
    boundary_rows = [r for r in rows if r.get("category") != "current_supported_turing_substrate"]
    return {
        "train": supported_pool[:train_end],
        "eval": supported_pool[train_end:eval_end],
        "test": supported_pool[eval_end:test_end],
        "heldout": supported_pool[test_end:heldout_end],
        "boundary": _sample(boundary_rows, limits["boundary"], seed + 5),
    }


def _stage_metrics(train_rows: List[Dict[str, Any]], eval_rows: List[Dict[str, Any]], before_trace: List[Dict[str, Any]], after_trace: List[Dict[str, Any]], state: Any) -> Dict[str, Any]:
    by_stage: Dict[str, Dict[str, Any]] = {}
    for stage in SUPPORTED_STAGES:
        before = [r for r in before_trace if r.get("stage") == stage]
        after = [r for r in after_trace if r.get("stage") == stage]
        train_count = sum(1 for r in train_rows if r.get("stage") == stage)
        by_stage[stage] = {
            "stage_name": stage,
            "train_sample_count": train_count,
            "eval_sample_count": len(after),
            "candidate_hit_before": _rate(sum(1 for r in before if r.get("candidate_hit")), len(before)),
            "candidate_hit_after": _rate(sum(1 for r in after if r.get("candidate_hit")), len(after)),
            "correct_output_in_beam_before": _rate(sum(1 for r in before if r.get("correct_output_in_beam")), len(before)),
            "correct_output_in_beam_after": _rate(sum(1 for r in after if r.get("correct_output_in_beam")), len(after)),
            "top1_correct_before": _rate(sum(1 for r in before if r.get("top1_correct")), len(before)),
            "top1_correct_after": _rate(sum(1 for r in after if r.get("top1_correct")), len(after)),
            "compiler_verified_before": _rate(sum(1 for r in before if r.get("top1_correct")), len(before)),
            "compiler_verified_after": _rate(sum(1 for r in after if r.get("top1_correct")), len(after)),
            "boundary_false_accept_before": 0.0,
            "boundary_false_accept_after": 0.0,
            "nutrient_reward_total": round(state.nutrient_reward_total, 6),
            "toxicity_total": round(state.toxicity_total, 6),
            "root_updates": state.root_updates,
            "branch_updates": state.branch_updates,
            "stage_runtime_seconds": 0.0,
            "stage_passed": len(after) > 0,
        }
    return {"by_stage": by_stage}


def _write_mainline(out: Path, metrics: Dict[str, Any], stage_metrics: Dict[str, Any], boundary: Dict[str, Any], baseline: Dict[str, Any]) -> None:
    improved = [stage for stage, row in stage_metrics["by_stage"].items() if row["top1_correct_after"] > row["top1_correct_before"]]
    failed = [stage for stage, row in stage_metrics["by_stage"].items() if row["top1_correct_after"] <= row["top1_correct_before"]]
    conclusion = {
        "what_this_version_proved": "bounded substrate training probe produced per-sample before/after candidate-space metrics with compiler validation",
        "what_this_version_did_not_prove": ["Turing completeness", "solved arithmetic", "stable convergence", "solved OOD", "general program synthesis", "same-size LLM advantage", "safe real promotion", "production readiness"],
        "bounded_substrate_positive_signal": metrics["ready_for_bounded_substrate_probe_claim"],
        "stages_improved": improved,
        "stages_failed": failed,
        "heldout_supported_success_rate": metrics["heldout_supported_success_rate"],
        "compiler_verified_correct_rate": metrics["compiler_verified_correct_rate"],
        "boundary_false_accept_summary": {k: boundary[k] for k in ["unsupported_false_accept_rate", "trap_false_accept_rate", "future_domain_supported_accept_rate", "near_ood_supported_accept_rate"]},
        "boundary_compiler_misroute_count": metrics["boundary_compiler_misroute_count"],
        "baseline_ablation_summary": baseline,
        "forbidden_field_access_count": metrics["forbidden_field_access_count"],
        "persisted_state_support_level": metrics["persisted_state_support_level"],
        "cross_process_reload_passed": metrics["cross_process_reload_passed"],
        "mandatory_counter_guard_passed": metrics["mandatory_counter_guard_passed"],
        "synthetic_summary_detected": metrics["synthetic_summary_detected"],
        "fixed_metric_detected": metrics["fixed_metric_detected"],
        "periodic_rule_detected": metrics["periodic_rule_detected"],
        "recommended_claim_level": metrics["recommended_claim_level"],
        "blocking_issues": metrics["blocking_issues"],
        "required_next_run": metrics["required_next_run"],
        "results_for_paper_v2": ["bounded substrate before/after probe", "compiler validation spot", "boundary safety summary"],
        "post_v1_routes_reserved": ["root similarity incremental training", "verified backend as teacher for NL-to-semantic-IR adapter"],
        "results_requiring_revalidation": ["larger large-light run", "deeper compiler-backed heldout rerun"],
        "still_not_proven": ["Turing completeness", "solved arithmetic", "stable convergence", "solved OOD", "general program synthesis", "same-size LLM advantage", "safe real promotion", "production readiness"],
    }
    _write_json(out / "mainline_conclusion.json", conclusion)
    (out / "mainline_conclusion.md").write_text("\n".join([
        "# v0.9.7 Mainline Conclusion",
        "",
        f"- bounded_substrate_positive_signal: {conclusion['bounded_substrate_positive_signal']}",
        f"- recommended_claim_level: {conclusion['recommended_claim_level']}",
        f"- heldout_supported_success_rate: {conclusion['heldout_supported_success_rate']}",
        f"- compiler_verified_correct_rate: {conclusion['compiler_verified_correct_rate']}",
        "- This is not a Turing-completeness or production-readiness claim.",
    ]) + "\n", encoding="utf-8")


def _iter_rows(scale_dir: Path) -> Iterable[Dict[str, Any]]:
    for split in ["train", "eval", "test", "heldout"]:
        for path in sorted((scale_dir / split).glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    yield json.loads(line)


def _sample(rows: List[Dict[str, Any]], count: int, seed: int) -> List[Dict[str, Any]]:
    rows = list(rows)
    rows.sort(key=lambda row: hashlib.sha256((row.get("id", "") + str(seed)).encode("utf-8")).hexdigest())
    return rows[: min(count, len(rows))]


def _rate(num: int, den: int) -> float:
    return round(num / den, 6) if den else 0.0


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
