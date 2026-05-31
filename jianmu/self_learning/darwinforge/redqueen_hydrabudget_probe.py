from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.hydrabudget_layer_monitor import build_hydrabudget_layer_monitor
from jianmu.self_learning.darwinforge.hydrabudget_threshold_sweep import run_hydrabudget_threshold_sweep
from jianmu.self_learning.darwinforge.redqueen_curriculum_audit import audit_redqueen_curriculum
from jianmu.self_learning.darwinforge.redqueen_curriculum_generator import generate_redqueen_curriculum
from jianmu.self_learning.darwinforge.redqueen_failure_miner import mine_redqueen_failures
from jianmu.self_learning.darwinforge.redqueen_hydrabudget_compiler_validation import run_redqueen_hydrabudget_compiler_validation
from jianmu.self_learning.darwinforge.redqueen_hydrabudget_eval import evaluate_redqueen_hydrabudget
from jianmu.self_learning.darwinforge.redqueen_hydrabudget_readiness import build_redqueen_hydrabudget_readiness, write_budget_expansion_safety_gate, write_data_contamination_gate, write_redqueen_hydrabudget_mainline, write_v0_9_17_historical_regression, write_v0_9_17_integrity, write_v0_9_17_persistence


def run_redqueen_hydrabudget_probe(source_records: str | Path, output_records: str | Path, output_redqueen_dataset: str | Path, experiment_groups: Iterable[str], budget_thresholds: Iterable[float], budget_multipliers: Iterable[float], modes: Iterable[str], compile_worker_count: int = 16, run_compiler_validation: bool = True, redqueen_scale_totals: Dict[str, int] | None = None) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    groups = list(experiment_groups)
    mode_list = list(modes)
    failure_mining = mine_redqueen_failures(source_records, out)
    redqueen_generation = generate_redqueen_curriculum(output_redqueen_dataset, out, failure_mining, scale_totals=redqueen_scale_totals)
    compiler = run_redqueen_hydrabudget_compiler_validation(output_redqueen_dataset, out, supported_spot=500, boundary_spot=500, compile_worker_count=compile_worker_count) if run_compiler_validation else {"compiler_validation_completed": False, "compiler_verified_correct_rate": 0.0}
    curriculum_audit = audit_redqueen_curriculum(output_redqueen_dataset, out, compiler.get("compiler_verified_correct_rate", 0.0))
    monitor = build_hydrabudget_layer_monitor(source_records, out)
    threshold_sweep = run_hydrabudget_threshold_sweep(out, monitor, budget_thresholds, budget_multipliers)
    best_threshold = threshold_sweep["best"]["utilization_threshold"]
    best_multiplier = threshold_sweep["best"]["budget_multiplier"]
    metrics = evaluate_redqueen_hydrabudget(out, groups, best_threshold, best_multiplier)
    best = max(metrics["runs"], key=lambda row: row["top1_after"])
    contamination = write_data_contamination_gate(out)
    budget_gate = write_budget_expansion_safety_gate(out, best)
    historical = write_v0_9_17_historical_regression(out, best["top1_after"], best["candidate_miss_after"])
    persistence = write_v0_9_17_persistence(out, best)
    integrity = write_v0_9_17_integrity(out, contamination, curriculum_audit["redqueen_audit_passed"])
    readiness = build_redqueen_hydrabudget_readiness(out, metrics, compiler, contamination, budget_gate, historical, persistence, integrity, failure_mining, curriculum_audit, mode_list, groups)
    mainline = write_redqueen_hydrabudget_mainline(out, readiness, failure_mining, curriculum_audit, threshold_sweep, budget_gate, compiler, historical, persistence)
    return {"failure_mining": failure_mining, "redqueen_generation": redqueen_generation, "curriculum_audit": curriculum_audit, "monitor": monitor, "threshold_sweep": threshold_sweep, "metrics": metrics, "compiler": compiler, "contamination": contamination, "budget_gate": budget_gate, "historical": historical, "persistence": persistence, "integrity": integrity, "readiness": readiness, "mainline": mainline}
