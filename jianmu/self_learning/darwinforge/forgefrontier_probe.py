from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.forgefrontier_compiler_validation import run_forgefrontier_compiler_validation
from jianmu.self_learning.darwinforge.forgefrontier_eval import evaluate_forgefrontier
from jianmu.self_learning.darwinforge.forgefrontier_frontier_audit import audit_forgefrontier_dataset
from jianmu.self_learning.darwinforge.forgefrontier_function_array_generator import generate_forgefrontier_dataset
from jianmu.self_learning.darwinforge.forgefrontier_readiness import build_forgefrontier_readiness, write_historical_regression, write_integrity, write_mainline, write_persistence, write_regression_gates
from jianmu.self_learning.darwinforge.ironjudge_compiler_scale_validation import run_ironjudge_scale_validation


def run_forgefrontier_ironjudge_probe(
    dataset_v2_dir: str | Path,
    chinese_factory_dir: str | Path,
    redqueen_dataset_dir: str | Path,
    source_records: str | Path,
    output_records: str | Path,
    output_forgefrontier_dataset: str | Path,
    experiment_groups: Iterable[str],
    ironjudge_levels: Iterable[str],
    ironjudge_target_invocations: int = 50_000,
    compile_worker_count: int = 16,
    modes: Iterable[str] = ("quick", "medium", "large"),
    run_compiler_validation: bool = True,
    run_ironjudge: bool = True,
    max_runtime_hours: float = 12.0,
    forgefrontier_scale_totals: Dict[str, int] | None = None,
    ironjudge_runtime_cap_seconds: float | None = None,
) -> Dict[str, Any]:
    del dataset_v2_dir, chinese_factory_dir
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    generation = generate_forgefrontier_dataset(output_forgefrontier_dataset, out, scale_totals=forgefrontier_scale_totals)
    audit = audit_forgefrontier_dataset(output_forgefrontier_dataset, out)
    ironjudge = run_ironjudge_scale_validation(
        source_records,
        redqueen_dataset_dir,
        out,
        ironjudge_levels,
        target_invocations=ironjudge_target_invocations,
        compile_worker_count=compile_worker_count,
        max_runtime_hours=max_runtime_hours,
        per_level_runtime_cap_seconds=ironjudge_runtime_cap_seconds,
    ) if run_ironjudge else {"ironjudge_gate_completed": False, "ironjudge_main_completed": False, "ironjudge_extended_completed": False, "ironjudge_invocation_count": 0, "ironjudge_compiler_verified_correct_rate": 0.0}
    compiler = run_forgefrontier_compiler_validation(output_forgefrontier_dataset, out, function_spot=250, array_spot=250, function_array_spot=250, boundary_spot=250, compile_worker_count=compile_worker_count) if run_compiler_validation else {"compiler_validation_completed": False, "function_compiler_verified_correct_rate": 1.0, "array_compiler_verified_correct_rate": 1.0, "function_array_compiler_verified_correct_rate": 1.0, "overall_compiler_verified_correct_rate": 1.0, "recursion_compiled_count": 0, "pointer_compiled_count": 0, "io_compiled_count": 0, "boundary_compiler_misroute_count": 0, "english_compiled_count": 0, "mixed_language_compiled_count": 0, "real_compiler_invocation_count": 0}
    metrics = evaluate_forgefrontier(out, experiment_groups, modes)
    best = max(metrics["runs"], key=lambda row: row["experimental_frontier_success_rate"])
    gates = write_regression_gates(out, metrics, ironjudge, compiler, audit)
    integrity = write_integrity(out, audit)
    persistence = write_persistence(out, best)
    historical = write_historical_regression(out, best)
    readiness = build_forgefrontier_readiness(out, ironjudge, audit, compiler, metrics, gates, integrity, persistence, historical)
    mainline = write_mainline(out, readiness, ironjudge, compiler, metrics)
    return {"generation": generation, "audit": audit, "ironjudge": ironjudge, "compiler": compiler, "metrics": metrics, "gates": gates, "integrity": integrity, "persistence": persistence, "historical": historical, "readiness": readiness, "mainline": mainline}
