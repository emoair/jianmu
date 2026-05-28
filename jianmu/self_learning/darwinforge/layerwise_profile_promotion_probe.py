from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.clean_msvc_preflight import run_clean_msvc_preflight
from jianmu.self_learning.darwinforge.layerwise_profile_compiler_validation import run_layerwise_profile_compiler_validation
from jianmu.self_learning.darwinforge.layerwise_profile_failure_analysis import write_layerwise_profile_failure_analysis
from jianmu.self_learning.darwinforge.layerwise_profile_persistence import write_layerwise_profile_state_and_reload
from jianmu.self_learning.darwinforge.layerwise_profile_promotion_readiness import build_layerwise_profile_promotion_readiness, write_layerwise_profile_integrity, write_layerwise_profile_mainline
from jianmu.self_learning.darwinforge.layerwise_profile_regression_gates import build_layerwise_profile_regression_gates
from jianmu.self_learning.darwinforge.layerwise_profile_resource_audit import build_layerwise_profile_resource_audit
from jianmu.self_learning.darwinforge.layerwise_profile_shadow_eval import PROMOTION_PROFILES, run_layerwise_profile_shadow_eval


def run_layerwise_profile_promotion_probe(
    frontier_dataset_dir: str | Path,
    source_records: str | Path,
    baseline_records: str | Path,
    output_records: str | Path,
    profiles: Iterable[str] = PROMOTION_PROFILES,
    samples: int = 20_000,
    boundary_samples: int = 20_000,
    compile_worker_count: int = 16,
    run_compiler_validation: bool = True,
    run_cross_process: bool = True,
    progress: bool = True,
    max_runtime_hours: float | None = None,
    checkpoint_interval_minutes: float | None = None,
    seeds: Iterable[int] = (88, 89, 90),
) -> Dict[str, Any]:
    del progress, max_runtime_hours, checkpoint_interval_minutes
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    required = [Path(source_records) / "layerwise_compiler_readiness.json", Path(baseline_records) / "adaptive_layerwise_metrics.json"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        return {"readiness": _missing(out, missing)}
    preflight = run_clean_msvc_preflight(out, Path.cwd())
    shadow = run_layerwise_profile_shadow_eval(frontier_dataset_dir, out, profiles, samples, boundary_samples, seeds)
    persistence = write_layerwise_profile_state_and_reload(out, shadow) if run_cross_process else {"cross_process_reload_passed": False}
    compiler = run_layerwise_profile_compiler_validation(frontier_dataset_dir, out, profiles, compile_worker_count, min(samples, 3000), min(boundary_samples, 3000), 5, 91) if run_compiler_validation and preflight.get("preflight_passed", False) else {"compiler_validation_completed": False, "compiler_verified_correct_rate": 0.0}
    resource = build_layerwise_profile_resource_audit(out, shadow, compiler, persistence)
    integrity = write_layerwise_profile_integrity(out)
    gates = build_layerwise_profile_regression_gates(out, shadow, compiler, persistence, resource, integrity)
    failure = write_layerwise_profile_failure_analysis(out, gates)
    readiness = build_layerwise_profile_promotion_readiness(out, shadow, gates, resource, compiler, persistence, integrity)
    conclusion = write_layerwise_profile_mainline(out, readiness, shadow, gates, resource, compiler, persistence, integrity)
    return {"preflight": preflight, "shadow": shadow, "persistence": persistence, "compiler": compiler, "resource": resource, "integrity": integrity, "gates": gates, "failure": failure, "readiness": readiness, "conclusion": conclusion}


def _missing(out: Path, missing: list[str]) -> Dict[str, Any]:
    import json

    result = {
        "promotion_probe_completed": False,
        "real_promotion_enabled": False,
        "profile_is_default_runtime": False,
        "recommended_claim_level": "layerwise_profile_promotion_probe_failed",
        "blocking_issues": ["missing_source_records"],
        "missing_source_records": missing,
        "ready_for_default_profile_dry_run": False,
    }
    (out / "layerwise_profile_promotion_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
