from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.opt_in_longhaul_execution import _execute_kind


def run_longhaul_replay(output_records: str | Path, rows: List[Dict[str, Any]], replay_samples: int = 5000, workers: int = 16, compiler_workers: int = 16) -> Dict[str, Any]:
    selected = _select(rows, replay_samples)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    workers_used = max(1, min(workers, compiler_workers, 16))
    replay_rows: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers_used) as pool:
        futures = [pool.submit(_replay_one, row, backend) for row in selected]
        for future in as_completed(futures):
            replay_rows.append(future.result())
    replay_rows.sort(key=lambda row: row["sample_id"])
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "longhaul_replay_manifest.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in replay_rows), encoding="utf-8")
    categories = {row["category"] for row in replay_rows}
    result = {
        "replay_validation_completed": True,
        "replay_sample_count": len(replay_rows),
        "replay_success_rate": round(sum(1 for row in replay_rows if row["replay_passed"]) / len(replay_rows), 6) if replay_rows else 0.0,
        "replay_fail_count": sum(1 for row in replay_rows if not row["replay_passed"]),
        "replay_stdout_mismatch_count": sum(1 for row in replay_rows if row["stdout_mismatch"]),
        "replay_source_hash_drift_count": sum(1 for row in replay_rows if row["source_hash_drift"]),
        "replay_policy_path_drift_count": sum(1 for row in replay_rows if row["policy_path_drift"]),
        "replay_ir_kind_drift_count": sum(1 for row in replay_rows if row["ir_kind_drift"]),
        "replay_compile_failure_count": sum(1 for row in replay_rows if row["compile_failure"]),
        "replay_timeout_count": sum(1 for row in replay_rows if row["timeout"]),
        "replay_all_categories_covered": {"default_blocking", "malformed_opt_in_blocking", "arithmetic", "function", "array", "function_array", "structured_recursion", "mixed", "opt_out_rollback", "post_rollback_default_blocking"} <= categories,
    }
    result["replay_passed"] = result["replay_fail_count"] == 0 and result["replay_all_categories_covered"]
    (out / "longhaul_replay_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _select(rows: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        by_cat.setdefault(row["category"], []).append(row)
    selected: List[Dict[str, Any]] = []
    per = max(1, count // max(1, len(by_cat)))
    for cat in sorted(by_cat):
        selected.extend(by_cat[cat][:per])
    index = 0
    while len(selected) < count and rows:
        selected.append(rows[index % len(rows)])
        index += 1
    return selected[:count]


def _replay_one(row: Dict[str, Any], backend: Any) -> Dict[str, Any]:
    index = int(str(row["sample_id"]).rsplit("_", 1)[-1])
    replay = _execute_kind(row["category"], index, backend, row["profile"])
    compiler_row = bool(row.get("compiler_invoked"))
    return {
        "sample_id": row["sample_id"],
        "category": row["category"],
        "policy": row["policy"],
        "expected_stdout": row["expected_stdout"],
        "actual_stdout": replay["actual_stdout"],
        "replay_passed": replay["actual_stdout"] == row["expected_stdout"] and replay["passed"],
        "stdout_mismatch": replay["actual_stdout"] != row["expected_stdout"],
        "source_hash_drift": compiler_row and replay["source_sha256"] != row["source_sha256"],
        "policy_path_drift": compiler_row and (replay["builder"] != row["builder"] or replay["emitter"] != row["emitter"]),
        "ir_kind_drift": compiler_row and replay["ir_kind"] != row["ir_kind"],
        "compile_failure": compiler_row and not replay["link_invoked"],
        "timeout": bool(replay["timeout"]),
    }
