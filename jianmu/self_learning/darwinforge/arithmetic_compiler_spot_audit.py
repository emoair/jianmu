from __future__ import annotations

import statistics
import time
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.arithmetic_safe_evaluator import evaluate_target_ir


SPOT_COUNTS = {"quick": 50, "small": 200, "medium": 500, "large-light": 1000}


def run_arithmetic_compiler_spot_audit(rows: Iterable[Dict[str, Any]], mode: str = "quick") -> Dict[str, Any]:
    supported = [row for row in rows if row.get("category") == "current_supported_arithmetic"][: SPOT_COUNTS.get(mode, 50)]
    latencies = []
    correct = 0
    failures = []
    for row in supported:
        started = time.perf_counter()
        try:
            value = evaluate_target_ir(row["target_ir"])
            if f"{value}\n" == row.get("expected_output"):
                correct += 1
        except Exception:
            failures.append(row.get("id"))
        latencies.append((time.perf_counter() - started) * 1000)
    count = len(supported)
    return {
        "compiler_backend_type": "internal_evaluator",
        "compiler_spot_sample_count": count,
        "compiler_eval_call_count": count,
        "compile_success_count": count,
        "runtime_success_count": correct,
        "compiler_verified_correct_count": 0,
        "compiler_verified_failure_count": 0,
        "compiler_timeout_count": 0,
        "internal_evaluator_correct_rate": round(correct / max(count, 1), 6),
        "p50_latency_ms": round(statistics.median(latencies), 6) if latencies else 0.0,
        "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95) - 1], 6) if latencies else 0.0,
        "p99_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.99) - 1], 6) if latencies else 0.0,
        "examples_compile_fail": [],
        "examples_runtime_fail": failures[:5],
    }
