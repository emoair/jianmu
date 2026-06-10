from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from jianmu.extended_emitter_c import ExtendedEmitterC
from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend, execute_with_backend
from jianmu.self_learning.darwinforge.extended_bridge_scale_validation import _program
from jianmu.self_learning.darwinforge.turing_substrate_compiler_validation import _compile_and_run_source


def run_trace_replay_validation(output_records: str | Path, samples: Iterable[Dict[str, object]], workers: int = 16, compiler_workers: int = 16) -> Dict[str, object]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    rows = list(samples)
    workers_used = max(1, min(int(workers), int(compiler_workers), 16))
    replay_rows: List[Dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=workers_used) as pool:
        futures = [pool.submit(_replay_one, row, backend) for row in rows]
        for fut in as_completed(futures):
            replay_rows.append(fut.result())
    replay_rows.sort(key=lambda row: str(row["review_sample_id"]))
    (out / "trace_replay_manifest.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in replay_rows), encoding="utf-8")
    result = _summary(replay_rows, workers, workers_used)
    (out / "trace_replay_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _replay_one(sample: Dict[str, object], backend) -> Dict[str, object]:
    policy = str(sample["policy"])
    source, expected, ir_kind, builder = _rebuild_source(policy, str(sample["source_trace_id"]))
    if policy == "canonical_arithmetic_targetir":
        actual = _run_arithmetic(source, expected, backend)
        compile_success = actual is not None
        timeout = False
    elif backend.backend_type == "real_c_compiler":
        result = _compile_and_run_source(source, backend, 5)
        actual = str(result.get("stdout_value_if_safe") or "").strip()
        compile_success = bool(result.get("compile_success"))
        timeout = bool(result.get("timeout"))
    else:
        actual = ""
        compile_success = False
        timeout = False
    expected_clean = expected.strip()
    source_hash = _hash(source)
    return {
        "review_sample_id": sample["review_sample_id"],
        "source_trace_id": sample["source_trace_id"],
        "policy": policy,
        "builder": builder,
        "ir_kind": ir_kind,
        "emitter": "ExtendedEmitterC" if policy != "canonical_arithmetic_targetir" else "existing_arithmetic_backend",
        "expected_stdout": expected_clean,
        "actual_stdout": actual,
        "original_source_sha256": sample["source_sha256"],
        "replay_source_sha256": source_hash,
        "replay_passed": actual == expected_clean and compile_success,
        "stdout_mismatch": actual != expected_clean,
        "source_hash_drift": source_hash != sample["source_sha256"],
        "policy_path_drift": builder != sample["builder"],
        "ir_kind_drift": ir_kind != sample["ir_kind"],
        "compile_failure": not compile_success,
        "timeout": timeout,
    }


def _run_arithmetic(source: str, expected: str, backend):
    parts = source.split("printf(\"%d\\n\", ", 1)
    expr = parts[1].split(");", 1)[0] if len(parts) == 2 else "0"
    result = execute_with_backend(expr, backend, 5)
    return str(result.get("stdout_value_if_safe") or "").strip()


def _rebuild_source(policy: str, sample_id: str) -> Tuple[str, str, str, str]:
    index = int(sample_id.rsplit("_", 1)[-1])
    if policy == "canonical_arithmetic_targetir":
        expr = f"{index % 101}+{(index * 5) % 97}"
        expected = str((index % 101) + ((index * 5) % 97)) + "\n"
        source = f"#include <stdio.h>\nint main(void) {{ printf(\"%d\\n\", {expr}); return 0; }}\n"
        return source, expected, "arithmetic", "existing_arithmetic_compiler_backend"
    kind = {
        "canonical_function_targetir": "function",
        "canonical_array_targetir": "array",
        "canonical_function_array_targetir": "function_array",
        "canonical_structured_recursion_targetir": "structured_recursion",
        "mixed_extended_ir_path": "mixed_extended",
    }[policy]
    program, expected, ir_kind, builder = _program(kind, index)
    return ExtendedEmitterC().emit(program), expected, ir_kind, builder


def _summary(rows: List[Dict[str, object]], workers_requested: int, workers_used: int) -> Dict[str, object]:
    count = len(rows)
    fails = [row for row in rows if not row["replay_passed"]]
    return {
        "replay_validation_completed": True,
        "replay_sample_count": count,
        "replay_pass_count": count - len(fails),
        "replay_fail_count": len(fails),
        "replay_success_rate": round((count - len(fails)) / count, 6) if count else 0.0,
        "replay_stdout_mismatch_count": sum(1 for row in rows if row["stdout_mismatch"]),
        "replay_source_hash_drift_count": sum(1 for row in rows if row["source_hash_drift"]),
        "replay_policy_path_drift_count": sum(1 for row in rows if row["policy_path_drift"]),
        "replay_ir_kind_drift_count": sum(1 for row in rows if row["ir_kind_drift"]),
        "replay_compile_failure_count": sum(1 for row in rows if row["compile_failure"]),
        "replay_timeout_count": sum(1 for row in rows if row["timeout"]),
        "workers_requested": workers_requested,
        "workers_used": workers_used,
        "downgrade_reason": "" if workers_used == workers_requested else "capped_for_thread_safe_local_compiler_replay",
    }


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

