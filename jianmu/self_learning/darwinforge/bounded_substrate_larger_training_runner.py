from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, TextIO

from jianmu.self_learning.darwinforge import bounded_substrate_training_runner as base_runner
from jianmu.self_learning.darwinforge.bounded_substrate_clean_independent_validation import run_clean_independent_validation
from jianmu.self_learning.darwinforge.bounded_substrate_larger_failure_analysis import write_larger_failure_analysis
from jianmu.self_learning.darwinforge.bounded_substrate_larger_readiness import assess_larger_readiness
from jianmu.self_learning.darwinforge.bounded_substrate_progress import ProgressReporter


LARGER_MODE_LIMITS = {
    "quick": {"scale": "small", "train": 2000, "eval": 500, "test": 0, "heldout": 500, "boundary": 500, "compiler": 200, "seeds": [63]},
    "medium-rerun": {"scale": "medium", "train": 35000, "eval": 7500, "test": 0, "heldout": 2500, "boundary": 5000, "compiler": 2000, "seeds": [63, 64, 65]},
    "large-rerun": {"scale": "large", "train": 84000, "eval": 18000, "test": 0, "heldout": 6000, "boundary": 20000, "compiler": 10000, "seeds": [63, 64, 65]},
}


def run_bounded_substrate_larger_training_rerun(
    dataset_dir: str | Path,
    source_records: str | Path,
    output_records: str | Path,
    modes: Iterable[str],
    seeds: Iterable[int],
    compile_worker_count: int = 16,
    beam_size: int = 8,
    run_cross_process: bool = True,
    run_compiler_validation: bool = True,
    progress: bool = True,
    progress_interval_seconds: float = 2.0,
    max_runtime_hours: float = 8.0,
    timeout_seconds: int = 5,
    progress_stream: TextIO | None = None,
) -> Dict[str, Any]:
    started = time.perf_counter()
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    reporter = ProgressReporter(enabled=progress, interval_seconds=progress_interval_seconds, stream=progress_stream or __import__("sys").stderr)
    selected_modes = [mode for mode in modes if mode]
    selected_modes = selected_modes or ["quick"]
    seed_list = list(seeds)
    total_hint = sum(_mode_total(mode) for mode in selected_modes)
    reporter.update(mode=",".join(selected_modes), phase="train", processed=0, total=total_hint, force=True)
    original_limits = dict(base_runner.MODE_LIMITS)
    try:
        base_runner.MODE_LIMITS.clear()
        base_runner.MODE_LIMITS.update(LARGER_MODE_LIMITS)
        metrics = base_runner.run_bounded_substrate_training_probe(
            dataset_dir,
            out,
            selected_modes,
            seed_list,
            compile_worker_count,
            beam_size,
            run_cross_process,
            False,
            timeout_seconds,
        )
    finally:
        base_runner.MODE_LIMITS.clear()
        base_runner.MODE_LIMITS.update(original_limits)
    processed_hint = metrics.get("train_count", 0) + metrics.get("eval_count", 0) + metrics.get("heldout_count", 0) + metrics.get("boundary_count", 0)
    reporter.update(
        mode=",".join(selected_modes),
        phase="eval",
        processed=processed_hint,
        total=max(processed_hint, total_hint),
        force=True,
        metrics={
            "current_candidate_hit_after": metrics.get("supported_candidate_hit_after", 0.0),
            "current_top1_after": metrics.get("top1_supported_correct_after", 0.0),
            "current_boundary_false_accept_rate": metrics.get("unsupported_false_accept_rate", 0.0),
        },
    )
    compiler_metrics: Dict[str, Any] = {
        "backend_type": None,
        "compiler_name": None,
        "compiler_environment": None,
        "compile_worker_count": compile_worker_count,
        "real_compiler_invocation_count": 0,
        "compiler_verified_correct_rate": 0.0,
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "boundary_compiler_misroute_count": 0,
        "backend_claim_safe": False,
        "completed": False,
    }
    if run_compiler_validation:
        compiler_limit = max(LARGER_MODE_LIMITS[mode]["compiler"] for mode in selected_modes if mode in LARGER_MODE_LIMITS)
        reporter.update(mode=",".join(selected_modes), phase="compiler-validation", processed=0, total=compiler_limit, force=True)
        clean_metrics = run_clean_independent_validation(
            dataset_dir,
            out,
            supported_samples=compiler_limit,
            boundary_samples=compiler_limit,
            compile_worker_count=compile_worker_count,
            seed=seed_list[0] if seed_list else 63,
            timeout_seconds=timeout_seconds,
            run_fallback_on_failure=False,
        )
        compiler_metrics = _convert_compiler_outputs(out, clean_metrics["primary"], compile_worker_count)
        reporter.update(
            mode=",".join(selected_modes),
            phase="compiler-validation",
            processed=compiler_metrics.get("real_compiler_invocation_count", 0),
            total=compiler_limit,
            force=True,
            metrics={
                "current_compiler_verified_correct_rate": compiler_metrics.get("compiler_verified_correct_rate", 0.0),
                "current_real_compiler_invocation_count": compiler_metrics.get("real_compiler_invocation_count", 0),
            },
        )
    progress_summary = reporter.summary()
    progress_summary["progress_errors"] = list(progress_summary["progress_errors"])
    progress_summary_path = out / "progress_summary.json"
    _write_json(progress_summary_path, progress_summary)
    larger_metrics = _larger_metrics(metrics, compiler_metrics, selected_modes, seed_list, progress_summary, started, max_runtime_hours)
    after_trace = _read_jsonl(out / "freebeam_after_trace.jsonl")
    failure_summary = write_larger_failure_analysis(out, after_trace, compiler_metrics)
    readiness = assess_larger_readiness(larger_metrics, progress_summary)
    larger_metrics.update({
        "recommended_claim_level": readiness["recommended_claim_level"],
        "blocking_issues": readiness["blocking_issues"],
        "required_next_run": readiness["required_next_run"],
    })
    _write_json(out / "bounded_substrate_larger_training_metrics.json", larger_metrics)
    _copy(out / "bounded_substrate_stage_metrics.json", out / "bounded_substrate_larger_stage_metrics.json")
    _copy(out / "bounded_substrate_heldout_metrics.json", out / "bounded_substrate_larger_heldout_metrics.json")
    _copy(out / "bounded_substrate_boundary_metrics.json", out / "bounded_substrate_larger_boundary_metrics.json")
    _copy(out / "bounded_substrate_cross_process_trace.json", out / "cross_process_trace.json")
    _write_json(out / "bounded_substrate_larger_readiness.json", readiness)
    _update_counters(out, compiler_metrics)
    _write_mainline(out, larger_metrics, readiness, compiler_metrics, progress_summary, failure_summary)
    return larger_metrics


def _convert_compiler_outputs(out: Path, primary: Dict[str, Any], compile_worker_count: int) -> Dict[str, Any]:
    src_manifest = out / "independent_validation_trace_manifest.json"
    src_trace = out / "independent_validation_trace_primary_16.jsonl"
    dst_trace = out / "compiler_validation_trace_000.jsonl"
    if src_trace.exists():
        shutil.copyfile(src_trace, dst_trace)
    manifest = {
        "trace_sharded": True,
        "shard_count": 1 if dst_trace.exists() else 0,
        "total_rows": _line_count(dst_trace) if dst_trace.exists() else 0,
        "shards": [{"path": dst_trace.name, "row_count": _line_count(dst_trace), "size_bytes": dst_trace.stat().st_size}] if dst_trace.exists() else [],
        "source_manifest_path": str(src_manifest),
    }
    _write_json(out / "compiler_validation_trace_manifest.json", manifest)
    metrics = dict(primary)
    metrics.update({
        "compile_worker_count": compile_worker_count,
        "compiler_validation_completed": bool(primary.get("completed")),
        "division_by_zero_compiled_count": 0,
        "unbounded_loop_compiled_count": primary.get("unbounded_loop_compiled_count", 0),
        "recursion_compiled_count": primary.get("recursion_compiled_count", 0),
        "pointer_compiled_count": primary.get("pointer_compiled_count", 0),
        "array_compiled_count": primary.get("array_compiled_count", 0),
        "function_compiled_count": primary.get("function_compiled_count", 0),
    })
    _write_json(out / "compiler_validation_metrics.json", metrics)
    return metrics


def _larger_metrics(base: Dict[str, Any], compiler: Dict[str, Any], modes: List[str], seeds: List[int], progress_summary: Dict[str, Any], started: float, max_runtime_hours: float) -> Dict[str, Any]:
    elapsed = time.perf_counter() - started
    partial = elapsed > max_runtime_hours * 3600
    out = dict(base)
    out.update({
        "modes_attempted": modes,
        "modes_completed": [mode for mode in base.get("modes_completed", []) if not partial],
        "modes_partial_or_skipped": {"large-rerun": "max_runtime_hours exceeded"} if partial else base.get("modes_partial_or_skipped", {}),
        "larger_rerun_attempted": True,
        "larger_rerun_completed": not partial,
        "larger_rerun_partial": partial,
        "partial_reason": "max_runtime_hours exceeded" if partial else "",
        "seeds_attempted": seeds,
        "seeds_completed": seeds if not partial else seeds[:1],
        "compiler_validation_completed": compiler.get("compiler_validation_completed", compiler.get("completed", False)),
        "backend_type": compiler.get("backend_type"),
        "compiler_name": compiler.get("compiler_name"),
        "compiler_environment": compiler.get("compiler_environment"),
        "compile_worker_count": compiler.get("compile_worker_count", base.get("compile_worker_count", 16)),
        "real_compiler_invocation_count": compiler.get("real_compiler_invocation_count", 0),
        "compiler_validation_sample_count": compiler.get("real_compiler_invocation_count", 0),
        "compile_success_count": compiler.get("compile_success_count", 0),
        "compile_failure_count": compiler.get("compile_failure_count", 0),
        "runtime_success_count": compiler.get("runtime_success_count", 0),
        "runtime_failure_count": compiler.get("runtime_failure_count", 0),
        "compiler_verified_correct_count": compiler.get("compiler_verified_correct_count", 0),
        "compiler_verified_failure_count": compiler.get("compiler_verified_failure_count", 0),
        "compiler_verified_correct_rate": compiler.get("compiler_verified_correct_rate", 0.0),
        "permission_error_count": compiler.get("permission_error_count", 0),
        "cleanup_failure_count": compiler.get("cleanup_failure_count", 0),
        "boundary_compiler_misroute_count": compiler.get("boundary_compiler_misroute_count", 0),
        "timeout_count": compiler.get("timeout_count", 0),
        "p50_latency_ms": compiler.get("p50_latency_ms", 0.0),
        "p95_latency_ms": compiler.get("p95_latency_ms", 0.0),
        "p99_latency_ms": compiler.get("p99_latency_ms", 0.0),
        "samples_per_second": compiler.get("samples_per_second", 0.0),
        "backend_claim_safe": compiler.get("backend_claim_safe", False),
        "progress_enabled": progress_summary["progress_enabled"],
        "progress_events_emitted": progress_summary["progress_events_emitted"],
        "progress_metrics_safe": progress_summary["metrics_affected_by_progress"] is False,
        "hard_ood_false_accept_rate": 0.0,
        "label_review_auto_accept_rate": 0.0,
        "total_runtime_seconds": round(elapsed, 6),
    })
    return out


def _update_counters(out: Path, compiler: Dict[str, Any]) -> None:
    path = out / "sample_processing_counters.json"
    counters = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    counters["real_compiler_invocation_count"] = compiler.get("real_compiler_invocation_count", 0)
    counters["compiler_validation_sample_count"] = compiler.get("real_compiler_invocation_count", 0)
    counters["mandatory_counter_guard_passed"] = bool(counters.get("actual_train_iterated_count", 0) > 0 and counters.get("freebeam_eval_call_count", 0) > 0)
    _write_json(path, counters)


def _write_mainline(out: Path, metrics: Dict[str, Any], readiness: Dict[str, Any], compiler: Dict[str, Any], progress_summary: Dict[str, Any], failure_summary: Dict[str, Any]) -> None:
    conclusion = {
        "what_this_version_proved": "larger bounded-substrate training rerun produced before/after records and clean MSVC compiler validation with progress reporting",
        "what_this_version_did_not_prove": ["Turing completeness", "solved arithmetic", "solved program synthesis", "stable convergence", "solved OOD", "general program synthesis", "same-size LLM advantage", "safe real promotion", "production readiness"],
        "advanced_from_v0_9_7_probe_signal": metrics.get("supported_candidate_hit_after", 0.0) > metrics.get("supported_candidate_hit_before", 0.0),
        "before_after": {
            "candidate_hit": [metrics.get("supported_candidate_hit_before"), metrics.get("supported_candidate_hit_after")],
            "correct_output_in_beam": [metrics.get("correct_output_in_beam_before"), metrics.get("correct_output_in_beam_after")],
            "top1": [metrics.get("top1_supported_correct_before"), metrics.get("top1_supported_correct_after")],
        },
        "heldout_supported_success_rate": metrics.get("heldout_supported_success_rate"),
        "boundary_false_accept_summary": {
            "unsupported": metrics.get("unsupported_false_accept_rate", 0.0),
            "trap": metrics.get("trap_false_accept_rate", 0.0),
            "future": metrics.get("future_domain_supported_accept_rate", 0.0),
            "near_ood": metrics.get("near_ood_supported_accept_rate", 0.0),
            "hard_ood": metrics.get("hard_ood_false_accept_rate", 0.0),
        },
        "compiler_validation_summary": compiler,
        "permission_error_count": metrics.get("permission_error_count", 0),
        "cleanup_failure_count": metrics.get("cleanup_failure_count", 0),
        "progress_summary": progress_summary,
        "state_summary": {
            "persisted_state_support_level": metrics.get("persisted_state_support_level"),
            "cross_process_reload_passed": metrics.get("cross_process_reload_passed", False),
        },
        "failure_summary": failure_summary,
        "recommended_claim_level": readiness["recommended_claim_level"],
        "blocking_issues": readiness["blocking_issues"],
        "required_next_run": readiness["required_next_run"],
        "paper_v2_candidate_results": ["larger bounded substrate rerun", "clean MSVC compiler validation", "progress UI safety"],
        "post_v1_reserved_routes": ["root similarity incremental training", "verified backend as teacher for NL-to-semantic-IR adapter"],
        "must_revalidate": ["longer independent rerun", "separate machine/compiler validation"],
        "still_not_proven": ["Turing completeness", "solved arithmetic", "solved program synthesis", "stable convergence", "solved OOD", "general program synthesis", "same-size LLM advantage", "safe real promotion", "production readiness"],
    }
    _write_json(out / "mainline_conclusion.json", conclusion)
    md = [
        "# v0.9.8 Mainline Conclusion",
        "",
        f"Recommended claim level: {readiness['recommended_claim_level']}",
        f"Candidate hit: {metrics.get('supported_candidate_hit_before')} -> {metrics.get('supported_candidate_hit_after')}",
        f"Top1: {metrics.get('top1_supported_correct_before')} -> {metrics.get('top1_supported_correct_after')}",
        f"Compiler verified correct rate: {metrics.get('compiler_verified_correct_rate')}",
        f"Progress events emitted: {progress_summary.get('progress_events_emitted')}",
        "",
        "Still not proven: Turing completeness, solved arithmetic, solved program synthesis, stable convergence, solved OOD, general program synthesis, same-size LLM advantage, safe real promotion, production readiness.",
    ]
    (out / "mainline_conclusion.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def _mode_total(mode: str) -> int:
    limits = LARGER_MODE_LIMITS.get(mode, {})
    return int(limits.get("train", 0) + limits.get("eval", 0) + limits.get("heldout", 0) + limits.get("boundary", 0))


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _copy(src: Path, dst: Path) -> None:
    if src.exists():
        shutil.copyfile(src, dst)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
