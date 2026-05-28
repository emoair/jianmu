from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.clean_msvc_preflight import run_clean_msvc_preflight
from jianmu.self_learning.darwinforge.default_profile_config_shadow import build_default_profile_dryrun_config
from jianmu.self_learning.darwinforge.default_profile_dryrun_compiler_validation import run_default_dryrun_compiler_validation
from jianmu.self_learning.darwinforge.default_profile_dryrun_eval import run_default_profile_dryrun_eval
from jianmu.self_learning.darwinforge.default_profile_fallback_rollback import run_fallback_rollback_dryrun
from jianmu.self_learning.darwinforge.historical_accuracy_regression import build_historical_accuracy_regression
from jianmu.self_learning.darwinforge.layerwise_profile_persistence import write_layerwise_profile_state_and_reload
from jianmu.self_learning.darwinforge.layerwise_profile_regression_gates import _gate
from jianmu.self_learning.darwinforge.layerwise_profile_resource_audit import build_layerwise_profile_resource_audit
from jianmu.self_learning.darwinforge.turing_frontier_v2_audit import audit_turing_frontier_v2_dataset
from jianmu.self_learning.darwinforge.turing_frontier_v2_coverage import summarize_turing_frontier_v2_coverage
from jianmu.self_learning.darwinforge.turing_frontier_v2_readiness import build_turing_frontier_v2_readiness
from jianmu.self_learning.darwinforge.v0_9_14_failure_analysis import run_dataset_v2_compiler_spot_audit
from jianmu.self_learning.darwinforge.v0_9_14_readiness import build_v0_9_14_integrity, build_v0_9_14_readiness, write_v0_9_14_mainline


def run_layerwise_default_profile_dryrun(
    frontier_dataset_dir: str | Path,
    frontier_v2_dir: str | Path,
    source_records: str | Path,
    baseline_records: str | Path,
    output_records: str | Path,
    profiles: Iterable[str],
    samples: int = 20_000,
    boundary_samples: int = 20_000,
    compile_worker_count: int = 16,
    run_compiler_validation: bool = True,
    run_cross_process: bool = True,
    run_fallback_rollback: bool = True,
    run_historical_regression: bool = True,
    run_dataset_v2_audit: bool = True,
    run_dataset_v2_compiler_spot: bool = True,
    seeds: Iterable[int] = (92, 93, 94),
) -> Dict[str, Any]:
    del source_records, baseline_records
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    config = build_default_profile_dryrun_config(out)
    preflight = run_clean_msvc_preflight(out, Path.cwd())
    eval_metrics = run_default_profile_dryrun_eval(frontier_dataset_dir, out, profiles, samples, boundary_samples, seeds)
    compiler = run_default_dryrun_compiler_validation(frontier_dataset_dir, out, profiles, compile_worker_count, min(samples, 3000), min(boundary_samples, 3000)) if run_compiler_validation and preflight.get("preflight_passed", False) else {"compiler_verified_correct_rate": 0.0}
    persistence = write_layerwise_profile_state_and_reload(out, _shadow_like(eval_metrics)) if run_cross_process else {"cross_process_reload_passed": False}
    fallback = run_fallback_rollback_dryrun(out, config) if run_fallback_rollback else {"fallback_rollback_gate_passed": False}
    resource = build_layerwise_profile_resource_audit(out, _shadow_like(eval_metrics), compiler, persistence)
    historical = build_historical_accuracy_regression(Path(output_records).parent, out, eval_metrics, compiler) if run_historical_regression else {"historical_regression_gate_passed": False}
    audit = audit_turing_frontier_v2_dataset(frontier_v2_dir, out) if run_dataset_v2_audit else {"scales": {}}
    coverage = summarize_turing_frontier_v2_coverage(frontier_v2_dir, out)
    spot = run_dataset_v2_compiler_spot_audit(frontier_v2_dir, out, compile_worker_count) if run_dataset_v2_compiler_spot else {"backend_claim_safe": False}
    dataset_ready = build_turing_frontier_v2_readiness(out, audit, coverage, spot)
    integrity = build_v0_9_14_integrity(out, config, dataset_ready)
    gates = _gates(out, config, eval_metrics, compiler, fallback, persistence, resource, integrity, historical)
    readiness = build_v0_9_14_readiness(out, config, eval_metrics, gates, historical, dataset_ready, integrity)
    conclusion = write_v0_9_14_mainline(out, readiness)
    return {"config": config, "preflight": preflight, "eval": eval_metrics, "compiler": compiler, "persistence": persistence, "fallback": fallback, "resource": resource, "historical": historical, "audit": audit, "coverage": coverage, "spot": spot, "dataset_ready": dataset_ready, "integrity": integrity, "gates": gates, "readiness": readiness, "conclusion": conclusion}


def _shadow_like(eval_metrics: Dict[str, Any]) -> Dict[str, Any]:
    rows = []
    for row in eval_metrics.get("profiles", []):
        mapped = dict(row)
        if mapped["profile_name"] == "layerwise_sparse_1B_freeze_prune_dryrun_default":
            mapped["profile_name"] = "layerwise_sparse_1B_freeze_prune"
        rows.append(mapped)
    return {"profiles": rows}


def _gates(out: Path, config: Dict[str, Any], eval_metrics: Dict[str, Any], compiler: Dict[str, Any], fallback: Dict[str, Any], persistence: Dict[str, Any], resource: Dict[str, Any], integrity: Dict[str, Any], historical: Dict[str, Any]) -> Dict[str, Any]:
    rows = {row["profile_name"]: row for row in eval_metrics["profiles"]}
    layer = rows["layerwise_sparse_1B_freeze_prune_dryrun_default"]
    combined = rows.get("combined_hot_rebalanced_balanced_sampling_1B", layer)
    current = rows.get("current_1B_reference", rows.get("actual_current_default_reference", layer))
    gates = {
        "shadow_default_gate": _gate(not config["real_promotion_enabled"] and config["actual_default_profile_unchanged"] and not config["profile_is_default_runtime"] and not config["production_config_modified"], config),
        "capability_gate": _gate(layer["top1_correct_rate"] >= 0.8274 - 0.01 and layer["top1_correct_rate"] > current["top1_correct_rate"] and layer["top1_correct_rate"] >= combined["top1_correct_rate"] and layer["candidate_miss_rate"] <= combined["candidate_miss_rate"], {"layerwise": layer, "combined": combined, "current": current}),
        "historical_regression_gate": _gate(historical.get("historical_regression_gate_passed", False), historical),
        "boundary_gate": _gate(layer["future_domain_supported_accept_rate"] == 0 and layer["boundary_false_accept_rate"] == 0 and layer["trap_false_accept_rate"] == 0 and layer["near_ood_supported_accept_rate"] <= 0.05, layer),
        "compiler_gate": _gate(compiler.get("compiler_verified_correct_rate", 0.0) >= 0.98 and compiler.get("permission_error_count", 0) == 0 and compiler.get("cleanup_failure_count", 0) == 0 and compiler.get("wrong_stdout_count", 0) == 0 and compiler.get("boundary_compiler_misroute_count", 0) == 0 and compiler.get("future_domain_compiled_count", 0) == 0, compiler),
        "fallback_rollback_gate": _gate(fallback.get("fallback_rollback_gate_passed", False), fallback),
        "persistence_gate": _gate(persistence.get("cross_process_reload_passed", False) and persistence.get("child_forbidden_field_access_count", 1) == 0, persistence),
        "resource_gate": _gate(resource.get("layerwise_resource_overhead_acceptable", False), resource),
        "integrity_gate": _gate(not integrity.get("real_promotion_enabled", True) and not integrity.get("profile_is_default_runtime", True) and integrity.get("forbidden_field_access_count", 1) == 0 and not integrity.get("fixed_metric_detected", True), integrity),
    }
    result = {"default_dryrun_gates_completed": True, **gates}
    _write_json(out / "default_dryrun_gates.json", result)
    (out / "default_dryrun_gates.md").write_text("# v0.9.14 Default Dry-Run Gates\n\nAll gates are dry-run gates. Real promotion remains disabled.\n", encoding="utf-8")
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
