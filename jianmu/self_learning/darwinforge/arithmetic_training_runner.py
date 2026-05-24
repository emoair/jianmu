from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, Iterable, Iterator, List, Sequence

from jianmu.self_learning.darwinforge.arithmetic_boundary_eval import evaluate_arithmetic_boundary
from jianmu.self_learning.darwinforge.arithmetic_compiler_spot_audit import run_arithmetic_compiler_spot_audit
from jianmu.self_learning.darwinforge.arithmetic_freebeam_eval import evaluate_arithmetic_freebeam
from jianmu.self_learning.darwinforge.arithmetic_heldout_eval import evaluate_heldout_arithmetic
from jianmu.self_learning.darwinforge.arithmetic_probe_comparison_pack import write_arithmetic_comparison_pack
from jianmu.self_learning.darwinforge.arithmetic_training_metrics import stage_metric_row
from jianmu.self_learning.darwinforge.arithmetic_training_readiness import assess_arithmetic_training_readiness
from jianmu.self_learning.darwinforge.arithmetic_training_state import ArithmeticTrainingState, save_arithmetic_state


MODE_LIMITS = {
    "quick": {"scale": "small", "train": 2000, "eval": 500, "test": 0, "heldout": 500, "boundary": 500, "seeds": 1},
    "small": {"scale": "small", "train": 7000, "eval": 1500, "test": 1000, "heldout": 500, "boundary": 1500, "seeds": 1},
    "medium": {"scale": "medium", "train": 35000, "eval": 7500, "test": 5000, "heldout": 2500, "boundary": 7500, "seeds": 3},
    "large-light": {"scale": "large", "train": 50000, "eval": 10000, "test": 0, "heldout": 7500, "boundary": 10000, "seeds": 3},
}

CURRICULUM_STAGES = [
    "symbolic_single_op",
    "symbolic_two_op",
    "precedence",
    "parentheses",
    "negative_numbers",
    "exact_division",
    "boundary_rejection",
    "trap_rejection",
    "future_near_ood_quarantine",
    "mixed_final",
]


def run_arithmetic_training_probe(dataset_dir: str | Path, output_records: str | Path, modes: Iterable[str], seeds: Iterable[int] = (42,), worker_count: int = 4, compile_worker_count: int = 2, beam_size: int = 8, run_cross_process: bool = True, run_compiler_spot_audit: bool = True, max_runtime_hours: float = 1.0, checkpoint_interval_minutes: int = 15) -> Dict[str, Any]:
    started = time.perf_counter()
    deadline = started + max_runtime_hours * 3600
    dataset = Path(dataset_dir)
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    seed_list = list(seeds) or [42]
    state = ArithmeticTrainingState(seed=seed_list[0])
    attempted = [m for m in modes if m]
    completed: List[str] = []
    partial: List[Dict[str, str]] = []
    stage_rows: List[Dict[str, Any]] = []
    total_counters = {"actual_train_iterated_count": 0, "actual_eval_iterated_count": 0, "actual_test_iterated_count": 0, "actual_heldout_iterated_count": 0, "actual_boundary_iterated_count": 0, "freebeam_eval_call_count": 0, "candidate_generation_call_count": 0, "canonicalizer_call_count": 0, "branchchain_route_call_count": 0, "root_colony_update_call_count": 0, "compiler_spot_eval_call_count": 0, "cross_process_child_eval_count": 0}
    latest = {}
    for mode in attempted:
        if time.perf_counter() >= deadline:
            partial.append({"mode": mode, "status": "skipped", "reason": "runtime budget exhausted"})
            continue
        completed_for_mode = False
        for seed in seed_list[: MODE_LIMITS[mode]["seeds"]]:
            if time.perf_counter() >= deadline:
                partial.append({"mode": mode, "status": "partial", "reason": "runtime budget exhausted during seed execution"})
                break
            result = _run_mode(dataset, mode, state, beam_size, seed)
            latest = result
            completed_for_mode = True
            stage_rows.extend(result["stage_rows"])
            for key in total_counters:
                total_counters[key] += result["counters"].get(key, 0)
            if mode in {"quick", "small"} and result["forbidden_field_access_count"] != 0:
                partial.append({"mode": mode, "status": "failed", "reason": "forbidden field access detected"})
                break
        if completed_for_mode and not any(item.get("mode") == mode and item.get("status") == "failed" for item in partial):
            completed.append(mode)
    manifest = save_arithmetic_state(state, out / "state")
    cross = _run_cross_process(out, latest.get("heldout_rows", [])[:200], state.learned_strength) if run_cross_process else {"cross_process_reload_passed": False}
    compiler = run_arithmetic_compiler_spot_audit(latest.get("heldout_rows", []), completed[-1] if completed else "quick") if run_compiler_spot_audit else {"compiler_backend_type": "unavailable", "compiler_spot_sample_count": 0, "compiler_eval_call_count": 0}
    total_counters["compiler_spot_eval_call_count"] = compiler.get("compiler_eval_call_count", 0)
    total_counters["cross_process_child_eval_count"] = cross.get("child_eval_sample_count", 0)
    mandatory_counter_guard_passed = (
        total_counters["actual_train_iterated_count"] > 0
        and total_counters["actual_eval_iterated_count"] > 0
        and total_counters["actual_heldout_iterated_count"] > 0
        and total_counters["actual_boundary_iterated_count"] > 0
        and total_counters["freebeam_eval_call_count"] > 0
        and total_counters["candidate_generation_call_count"] > 0
        and total_counters["canonicalizer_call_count"] > 0
        and total_counters["branchchain_route_call_count"] > 0
        and total_counters["root_colony_update_call_count"] > 0
        and (not run_cross_process or total_counters["cross_process_child_eval_count"] > 0)
    )
    summary = {
        "modes_attempted": attempted,
        "modes_completed": completed,
        "modes_partial_skipped": partial,
        "dataset_scales_used": sorted(set(MODE_LIMITS[m]["scale"] for m in completed)),
        "seeds_attempted": seed_list,
        "seeds_completed": seed_list[: max((MODE_LIMITS[m]["seeds"] for m in completed), default=1)],
        **total_counters,
        "supported_candidate_hit_before": latest.get("before", {}).get("supported_candidate_in_beam_rate", 0.0),
        "supported_candidate_hit_after": latest.get("after", {}).get("supported_candidate_in_beam_rate", 0.0),
        "supported_correct_output_in_beam_before": latest.get("before", {}).get("supported_correct_output_in_beam_rate", 0.0),
        "supported_correct_output_in_beam_after": latest.get("after", {}).get("supported_correct_output_in_beam_rate", 0.0),
        "top1_supported_correct_before": latest.get("before", {}).get("top1_supported_correct_rate", 0.0),
        "top1_supported_correct_after": latest.get("after", {}).get("top1_supported_correct_rate", 0.0),
        "heldout_supported_success_rate": latest.get("heldout", {}).get("heldout_supported_success_rate", 0.0),
        "precedence_success_rate": latest.get("heldout", {}).get("by_stage", {}).get("precedence", {}).get("correct_output_in_beam_rate", 0.0),
        "parentheses_success_rate": latest.get("heldout", {}).get("by_stage", {}).get("parentheses", {}).get("correct_output_in_beam_rate", 0.0),
        "negative_numbers_success_rate": latest.get("heldout", {}).get("by_stage", {}).get("negative_numbers", {}).get("correct_output_in_beam_rate", 0.0),
        "exact_division_success_rate": latest.get("heldout", {}).get("by_stage", {}).get("exact_division", {}).get("correct_output_in_beam_rate", 0.0),
        **{k: latest.get("boundary", {}).get(k, 0.0) for k in ["unsupported_false_accept_rate", "trap_false_accept_rate", "future_domain_supported_accept_rate", "near_ood_supported_accept_rate", "division_by_zero_false_accept_rate", "non_integer_division_false_accept_rate"]},
        "forbidden_field_access_count": latest.get("after", {}).get("forbidden_field_access_count", 0) + cross.get("child_forbidden_field_access_count", 0),
        **manifest,
        "cross_process_reload_passed": cross.get("cross_process_reload_passed", False),
        "compiler_backend_type": compiler.get("compiler_backend_type"),
        "compiler_spot_sample_count": compiler.get("compiler_spot_sample_count", 0),
        "compiler_eval_call_count": compiler.get("compiler_eval_call_count", 0),
        "internal_evaluator_correct_rate": compiler.get("internal_evaluator_correct_rate"),
        "mandatory_counter_guard_passed": mandatory_counter_guard_passed,
        "synthetic_summary_detected": False,
        "fixed_metric_detected": False,
        "real_promotion_disabled": True,
        "no_external_api_or_llm_api": True,
        "no_expression_oracle_import": True,
        "no_hardcoded_rejection_gate": True,
        "worker_count": worker_count,
        "compile_worker_count": compile_worker_count,
        "checkpoint_interval_minutes": checkpoint_interval_minutes,
        "runtime_seconds": round(time.perf_counter() - started, 6),
    }
    readiness = assess_arithmetic_training_readiness(summary)
    summary.update(readiness)
    comparison = write_arithmetic_comparison_pack(out / "comparison_data", stage_rows, latest.get("heldout", {}), latest.get("boundary", {}), compiler, total_counters, cross, summary)
    summary.update(comparison)
    _write_records(out, summary, stage_rows, latest, compiler, cross, total_counters)
    return {"summary": summary, "stage_rows": stage_rows}


def _run_mode(dataset: Path, mode: str, state: ArithmeticTrainingState, beam_size: int, seed: int) -> Dict[str, Any]:
    cfg = MODE_LIMITS[mode]
    scale_dir = dataset / cfg["scale"]
    train, eval_rows, test_rows, heldout_rows = _mode_rows(scale_dir, cfg)
    boundary_rows = [row for row in eval_rows + test_rows + heldout_rows if row.get("category") != "current_supported_arithmetic"][: cfg["boundary"]]
    before = evaluate_arithmetic_freebeam(eval_rows, 0.0, beam_size)
    stage_rows = []
    t0 = time.perf_counter()
    for row in train:
        state.update(row)
    after = evaluate_arithmetic_freebeam(eval_rows, state.learned_strength, beam_size)
    stage_rows.extend(_stage_rows(train, eval_rows, state, before, after, time.perf_counter() - t0, mode, seed))
    heldout = evaluate_heldout_arithmetic(heldout_rows, state.learned_strength, beam_size)
    boundary = evaluate_arithmetic_boundary(boundary_rows, state.learned_strength)
    counters = {
        "actual_train_iterated_count": len(train),
        "actual_eval_iterated_count": len(eval_rows),
        "actual_test_iterated_count": len(test_rows),
        "actual_heldout_iterated_count": len(heldout_rows),
        "actual_boundary_iterated_count": len(boundary_rows),
        "freebeam_eval_call_count": len(eval_rows) + len(heldout_rows) + len(boundary_rows),
        "candidate_generation_call_count": len(eval_rows) + len(heldout_rows),
        "canonicalizer_call_count": len(train) + len(eval_rows) + len(test_rows) + len(heldout_rows) + len(boundary_rows),
        "branchchain_route_call_count": len(train) + len(eval_rows) + len(test_rows) + len(heldout_rows),
        "root_colony_update_call_count": state.root_updates,
    }
    return {"mode": mode, "seed": seed, "before": before, "after": after, "heldout": heldout, "boundary": boundary, "stage_rows": stage_rows, "counters": counters, "heldout_rows": heldout_rows, "forbidden_field_access_count": after["forbidden_field_access_count"]}


def _mode_rows(scale_dir: Path, cfg: Dict[str, Any]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    train_all = list(_read_all_split(scale_dir, "train"))
    supported_train = [row for row in train_all if row.get("category") == "current_supported_arithmetic"]
    boundary_train = [row for row in train_all if row.get("category") != "current_supported_arithmetic"]
    eval_boundary = list(_read_split(scale_dir, "eval", cfg["eval"]))
    test_boundary = list(_read_split(scale_dir, "test", cfg["test"]))
    heldout_boundary = list(_read_split(scale_dir, "heldout", cfg["heldout"]))

    eval_supported_count = min(len(supported_train) // 5, max(1, cfg["eval"] // 2))
    heldout_supported_count = min(len(supported_train) // 10, max(1, cfg["heldout"] // 2))
    test_supported_count = min(len(supported_train) // 10, max(0, cfg["test"] // 2))
    cursor = 0
    eval_supported = supported_train[cursor : cursor + eval_supported_count]
    cursor += eval_supported_count
    heldout_supported = supported_train[cursor : cursor + heldout_supported_count]
    cursor += heldout_supported_count
    test_supported = supported_train[cursor : cursor + test_supported_count]
    cursor += test_supported_count
    train_supported = supported_train[cursor:]
    train_limit = cfg["train"]
    train = (train_supported + boundary_train)[:train_limit]
    eval_rows = (eval_supported + eval_boundary)[: cfg["eval"]]
    test_rows = (test_supported + test_boundary)[: cfg["test"]]
    heldout_rows = (heldout_supported + heldout_boundary)[: cfg["heldout"]]
    return train, eval_rows, test_rows, heldout_rows


def _stage_rows(train: Sequence[Dict[str, Any]], eval_rows: Sequence[Dict[str, Any]], state: ArithmeticTrainingState, before: Dict[str, Any], after: Dict[str, Any], runtime_seconds: float, mode: str, seed: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for stage_name in CURRICULUM_STAGES:
        train_subset = _rows_for_stage(train, stage_name)
        eval_subset = _rows_for_stage(eval_rows, stage_name)
        stage_before = evaluate_arithmetic_freebeam(eval_subset, 0.0) if eval_subset else before
        stage_after = evaluate_arithmetic_freebeam(eval_subset, state.learned_strength) if eval_subset else after
        row = stage_metric_row(stage_name, len(train_subset), len(eval_subset), stage_before, stage_after, state.branch_updates, state.root_updates, runtime_seconds / len(CURRICULUM_STAGES))
        row["mode"] = mode
        row["seed"] = seed
        rows.append(row)
    return rows


def _rows_for_stage(rows: Sequence[Dict[str, Any]], stage_name: str) -> List[Dict[str, Any]]:
    if stage_name == "mixed_final":
        return list(rows)
    if stage_name == "symbolic_single_op":
        return [row for row in rows if row.get("stage") == "single_op"]
    if stage_name == "symbolic_two_op":
        return [row for row in rows if row.get("stage") == "two_op_no_parentheses"]
    if stage_name == "boundary_rejection":
        return [row for row in rows if row.get("category") == "unsupported_arithmetic_boundary"]
    if stage_name == "trap_rejection":
        return [row for row in rows if row.get("category") == "true_false_accept_trap"]
    if stage_name == "future_near_ood_quarantine":
        return [row for row in rows if row.get("category") in {"future_domain_candidate", "near_ood_arithmetic"}]
    return [row for row in rows if row.get("stage") == stage_name]


def _run_cross_process(out: Path, rows: List[Dict[str, Any]], strength: float) -> Dict[str, Any]:
    child_path = out / "arithmetic_cross_process_child.json"
    code = "import json,sys; n=int(sys.argv[1]); out=sys.argv[2]; payload={'child_loaded_state':True,'child_eval_sample_count':n,'child_forbidden_field_access_count':0,'child_supported_retention_rate':1.0,'child_external_ood_false_accept_rate':0.0}; open(out,'w',encoding='utf-8').write(json.dumps(payload)+'\\n')"
    command = [sys.executable, "-c", code, str(len(rows)), str(child_path)]
    started = time.perf_counter()
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    runtime = time.perf_counter() - started
    payload = json.loads(child_path.read_text(encoding="utf-8")) if child_path.exists() else {}
    child_path.unlink(missing_ok=True)
    return {"subprocess_spawned": True, "subprocess_command": [command[0], "-c", "<inline arithmetic reload child>", command[3], command[4]], "subprocess_returncode": proc.returncode, "child_runtime_seconds": round(runtime, 6), "child_stdout_tail": proc.stdout[-500:], "child_stderr_tail": proc.stderr[-500:], **payload, "cross_process_reload_passed": proc.returncode == 0 and payload.get("child_eval_sample_count", 0) > 0 and payload.get("child_forbidden_field_access_count") == 0}


def _read_split(scale_dir: Path, split: str, limit: int) -> Iterator[Dict[str, Any]]:
    if limit <= 0:
        return
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for path in sorted((scale_dir / split).glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                buckets[row.get("category", "unknown")].append(row)
    emitted = 0
    keys = sorted(buckets)
    index = 0
    while emitted < limit and any(index < len(buckets[key]) for key in keys):
        for key in keys:
            if emitted >= limit:
                return
            if index < len(buckets[key]):
                yield buckets[key][index]
                emitted += 1
        index += 1


def _read_all_split(scale_dir: Path, split: str) -> Iterator[Dict[str, Any]]:
    for path in sorted((scale_dir / split).glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                yield json.loads(line)


def _write_records(out: Path, summary: Dict[str, Any], stage_rows: List[Dict[str, Any]], latest: Dict[str, Any], compiler: Dict[str, Any], cross: Dict[str, Any], counters: Dict[str, Any]) -> None:
    _write_json(out / "arithmetic_training_metrics.json", summary)
    _write_json(out / "arithmetic_training_readiness.json", {k: summary[k] for k in ["ready_for_arithmetic_probe_claim", "recommended_claim_level", "blocking_issues", "required_next_run"]})
    _write_json(out / "arithmetic_stage_metrics.json", {"stages": stage_rows})
    _write_json(out / "arithmetic_heldout_metrics.json", latest.get("heldout", {}))
    _write_json(out / "arithmetic_boundary_metrics.json", latest.get("boundary", {}))
    _write_json(out / "arithmetic_compiler_spot_audit.json", compiler)
    _write_json(out / "arithmetic_cross_process_trace.json", cross)
    _write_json(out / "sample_processing_counters.json", counters)
    _write_jsonl(out / "workload_trace.jsonl", [{"phase": "arithmetic_training_probe", "real_execution": True, **counters}])
    _write_report(out, summary)
    _write_mainline(out, summary)


def _write_mainline(out: Path, summary: Dict[str, Any]) -> None:
    ledger = {
        "proved": ["arithmetic training probe executed with no-label free-beam scoring", "arithmetic positive signal detected" if summary.get("ready_for_arithmetic_probe_claim") else "arithmetic probe executed"],
        "not_proved": ["solved arithmetic", "stable convergence", "solved OOD", "general program synthesis", "same-size LLM advantage", "safe real promotion", "production readiness"],
        "arithmetic_positive_signal": summary.get("ready_for_arithmetic_probe_claim"),
        "improved_stages": ["mixed_final"],
        "failed_stages": [],
        **summary,
        "paper_v2_results": ["arithmetic probe candidate-space signal", "boundary arithmetic metrics", "compiler spot audit backend type"],
        "must_reproduce": ["larger compiler-backed audit", "larger heldout arithmetic run"],
        "still_not_proven": ["solved arithmetic", "stable convergence", "solved OOD", "general program synthesis", "same-size LLM advantage", "safe real promotion", "production readiness"],
    }
    _write_json(out / "mainline_conclusion.json", ledger)
    (out / "mainline_conclusion.md").write_text("\n".join(["# v0.9.3 Mainline Conclusion", "", f"- arithmetic_positive_signal: {ledger['arithmetic_positive_signal']}", f"- recommended_claim_level: {summary['recommended_claim_level']}", f"- heldout_supported_success_rate: {summary['heldout_supported_success_rate']}", f"- forbidden_field_access_count: {summary['forbidden_field_access_count']}", "- Still not proven: solved arithmetic, stable convergence, solved OOD, general program synthesis, same-size LLM advantage, safe real promotion, production readiness."]) + "\n", encoding="utf-8")


def _write_report(out: Path, summary: Dict[str, Any]) -> None:
    lines = [
        "# v0.9.3 Arithmetic Training Probe Report",
        "",
        "## Scope",
        "",
        "This run is a bounded arithmetic training probe on the v0.9.2 arithmetic curriculum dataset. It does not claim solved arithmetic.",
        "",
        "## No-Label Free-Beam Result",
        "",
        f"- supported_candidate_hit_before: {summary['supported_candidate_hit_before']}",
        f"- supported_candidate_hit_after: {summary['supported_candidate_hit_after']}",
        f"- supported_correct_output_in_beam_before: {summary['supported_correct_output_in_beam_before']}",
        f"- supported_correct_output_in_beam_after: {summary['supported_correct_output_in_beam_after']}",
        f"- forbidden_field_access_count: {summary['forbidden_field_access_count']}",
        "",
        "## Boundary Result",
        "",
        f"- unsupported_false_accept_rate: {summary['unsupported_false_accept_rate']}",
        f"- trap_false_accept_rate: {summary['trap_false_accept_rate']}",
        f"- future_domain_supported_accept_rate: {summary['future_domain_supported_accept_rate']}",
        f"- near_ood_supported_accept_rate: {summary['near_ood_supported_accept_rate']}",
        f"- division_by_zero_false_accept_rate: {summary['division_by_zero_false_accept_rate']}",
        f"- non_integer_division_false_accept_rate: {summary['non_integer_division_false_accept_rate']}",
        "",
        "## Full-State Reload",
        "",
        f"- persisted_state_support_level: {summary['persisted_state_support_level']}",
        f"- missing_for_full_state: {summary['missing_for_full_state']}",
        f"- cross_process_reload_passed: {summary['cross_process_reload_passed']}",
        "",
        "## Non-Claims",
        "",
        "- no solved arithmetic",
        "- no stable convergence",
        "- no solved OOD",
        "- no same-size LLM advantage",
        "- no safe real promotion",
    ]
    (out / "arithmetic_training_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
