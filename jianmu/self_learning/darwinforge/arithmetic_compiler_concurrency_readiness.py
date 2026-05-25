from __future__ import annotations

from typing import Any, Dict, List


def assess_compiler_concurrency_readiness(metrics: Dict[str, Any]) -> Dict[str, Any]:
    levels = metrics.get("levels", [])
    completed = [row for row in levels if row.get("completed")]
    stable = [row for row in completed if row.get("stable")]
    unstable = [row for row in levels if not row.get("stable")]
    blocking: List[str] = []

    if metrics.get("backend_type") != "real_c_compiler":
        blocking.append("real_compiler_unavailable")
        claim = "compiler_unavailable"
    elif len([row for row in completed if row.get("compile_worker_count") in {4, 8, 16, 32}]) < 4:
        blocking.append("required_low_worker_levels_incomplete")
        claim = "failed"
    elif any(row.get("boundary_compiler_misroute_count", 0) for row in completed):
        blocking.append("boundary_compiler_misroute_detected")
        claim = "failed"
    else:
        baseline = next((row for row in completed if row.get("compile_worker_count") == 4), None)
        improved = any((row.get("samples_per_second") or 0) > (baseline or {}).get("samples_per_second", 0) for row in completed if row.get("compile_worker_count") != 4)
        high_stable = [row for row in stable if row.get("compile_worker_count", 0) >= 128]
        high_errors = any(
            row.get("timeout_count", 0) or row.get("process_spawn_error_count", 0) or row.get("compile_failure_count", 0) or row.get("runtime_failure_count", 0)
            for row in high_stable
        )
        if high_stable and improved and not high_errors:
            claim = "high_concurrency_stable"
        elif improved and not high_stable:
            claim = "compiler_concurrency_scaling_profile_established"
        elif high_stable and high_errors:
            claim = "high_concurrency_unstable"
        else:
            claim = "high_concurrency_unstable"

    best = max(stable or completed or [{}], key=lambda row: row.get("samples_per_second") or 0)
    stable_worker_levels = [row.get("compile_worker_count") for row in stable]
    unstable_worker_levels = [
        {"compile_worker_count": row.get("compile_worker_count"), "unstable_reason": row.get("unstable_reason", "not_stable")}
        for row in levels
        if not row.get("stable")
    ]
    return {
        "scaling_completed": bool(completed),
        "tested_worker_levels": [row.get("compile_worker_count") for row in levels],
        "stable_worker_levels": stable_worker_levels,
        "unstable_worker_levels": unstable_worker_levels,
        "best_compile_worker_count": best.get("compile_worker_count"),
        "best_samples_per_second": best.get("samples_per_second"),
        "best_latency_profile": {key: best.get(key) for key in ["p50_latency_ms", "p95_latency_ms", "p99_latency_ms"]},
        "recommended_default_compile_worker_count": best.get("compile_worker_count"),
        "max_stable_compile_worker_count": max(stable_worker_levels) if stable_worker_levels else None,
        "compiler_verified_correct_rate_at_best": best.get("compiler_verified_correct_rate"),
        "boundary_compiler_misroute_count_at_best": best.get("boundary_compiler_misroute_count"),
        "timeout_count_at_best": best.get("timeout_count"),
        "process_spawn_error_count_at_best": best.get("process_spawn_error_count"),
        "trace_write_error_count_at_best": best.get("trace_write_error_count"),
        "recommended_claim_level": claim,
        "blocking_issues": sorted(set(blocking)),
        "required_next_run": "rerun best worker level with larger samples; keep conservative arithmetic and Turing-completeness wording",
    }
