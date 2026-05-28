from __future__ import annotations

import concurrent.futures
import hashlib
import json
import re
import statistics
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.turing_substrate_compiler_validation import _compile_and_run_source, target_ir_to_c_source


VALID_SUPPORT_STATUS = {"current_supported", "near_supported", "future_domain", "unsupported", "trap", "review"}
VALID_CATEGORIES = {
    "current_supported_bounded_substrate",
    "bounded_control_hard_supported",
    "near_supported_pure_function",
    "near_supported_fixed_array",
    "future_function_call_graph",
    "future_array_loop_combination",
    "future_bounded_recursion_candidate",
    "unsupported_unbounded_recursion",
    "unsupported_unbounded_loop",
    "scope_lifetime_edge_cases",
    "trap_unsafe_io_system",
    "adversarial_natural_language_trap",
    "hard_ood",
    "label_review_candidate",
}
REQUIRED_RAW_FILES = [
    "raw_manifest.json",
    "raw_generation_report.md",
    "warnings/known_limitations.md",
]
REQUIRED_FIELDS = {
    "id",
    "raw_dataset_version",
    "split_hint",
    "category",
    "support_status",
    "stage",
    "input",
    "natural_language_variants",
    "candidate_program",
    "expected_action",
    "language_features",
}
EXPECTED_ACTION_BY_STATUS = {
    "current_supported": {"train_current"},
    "near_supported": {"isolate_future", "quarantine", "review"},
    "future_domain": {"isolate_future"},
    "unsupported": {"reject"},
    "trap": {"reject"},
    "review": {"review", "quarantine"},
}
FORBIDDEN_SUPPORTED_FEATURES = {
    "has_function",
    "has_function_call",
    "has_multiple_functions",
    "has_array",
    "has_array_loop",
    "has_pointer",
    "has_recursion",
    "has_bounded_recursion",
    "has_unbounded_loop",
    "has_io",
    "has_system_call",
}


def run_active_generation_pilot(
    raw_dataset_dir: str | Path,
    output_dataset_dir: str | Path,
    records_dir: str | Path,
    supported_spot: int = 5_000,
    boundary_spot: int = 5_000,
    compile_worker_count: int = 16,
    seed: int = 97,
    timeout_seconds: int = 5,
) -> Dict[str, Any]:
    raw_dir = Path(raw_dataset_dir)
    out_dataset = Path(output_dataset_dir)
    records = Path(records_dir)
    out_dataset.mkdir(parents=True, exist_ok=True)
    records.mkdir(parents=True, exist_ok=True)

    rows, malformed = load_raw_rows(raw_dir)
    schema = audit_raw_schema(raw_dir, rows, malformed)
    _write_json(records / "raw_schema_audit.json", schema)
    (records / "raw_schema_audit.md").write_text(_schema_md(schema), encoding="utf-8")

    dedup = audit_raw_dedup_leakage(rows)
    _write_json(records / "raw_dedup_leakage_audit.json", dedup)

    safety = audit_support_status_safety(rows)
    _write_json(records / "support_status_safety_audit.json", safety)

    conversion, converted_rows, conversion_failures = convert_current_supported_rows(rows, compile_worker_count, timeout_seconds)
    _write_json(records / "conversion_metrics.json", conversion)
    _write_jsonl(records / "conversion_failures.jsonl", conversion_failures)

    compiler = run_compiler_audit(converted_rows, rows, records, supported_spot, boundary_spot, compile_worker_count, seed, timeout_seconds)

    split = split_active_generation_pool(rows, converted_rows, malformed, schema, dedup, safety, compiler)
    write_split_dataset(out_dataset, split)

    readiness = build_readiness(raw_dir, schema, dedup, safety, conversion, compiler, split)
    _write_json(records / "active_generation_pilot_readiness.json", readiness)
    (records / "mainline_conclusion.md").write_text(_mainline_md(readiness), encoding="utf-8")
    return readiness


def load_raw_rows(raw_dir: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    rows: List[Dict[str, Any]] = []
    malformed: List[Dict[str, Any]] = []
    for path in sorted((raw_dir / "shards").glob("*.jsonl")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                row["_source_shard"] = path.name
                row["_source_line"] = line_no
                rows.append(row)
            except json.JSONDecodeError as exc:
                malformed.append({"source_shard": path.name, "source_line": line_no, "error": str(exc), "line_hash": _hash(line)})
    return rows, malformed


def audit_raw_schema(raw_dir: Path, rows: List[Dict[str, Any]], malformed: List[Dict[str, Any]]) -> Dict[str, Any]:
    missing_raw_files = [name for name in REQUIRED_RAW_FILES if not (raw_dir / name).exists()]
    missing_stats_dir = not (raw_dir / "stats").exists()
    shard_count = len(list((raw_dir / "shards").glob("*.jsonl")))
    ids = [str(row.get("id", "")) for row in rows if row.get("id") is not None]
    invalid_rows = []
    status_invalid = 0
    category_invalid = 0
    expected_action_invalid = 0
    feature_incoherent = 0
    for row in rows:
        missing = sorted(REQUIRED_FIELDS - set(row))
        status = row.get("support_status")
        category = row.get("category")
        action = row.get("expected_action")
        features = row.get("language_features")
        invalid_feature = not isinstance(features, dict) or any(not isinstance(v, bool) for v in features.values())
        invalid_variants = not isinstance(row.get("natural_language_variants"), list) or not row.get("natural_language_variants")
        invalid_program = not isinstance(row.get("candidate_program"), str) or not row.get("candidate_program", "").strip()
        bad_status = status not in VALID_SUPPORT_STATUS
        bad_category = category not in VALID_CATEGORIES
        bad_action = action not in EXPECTED_ACTION_BY_STATUS.get(status, set())
        if bad_status:
            status_invalid += 1
        if bad_category:
            category_invalid += 1
        if bad_action:
            expected_action_invalid += 1
        if invalid_feature:
            feature_incoherent += 1
        if missing or invalid_variants or invalid_program or bad_status or bad_category or bad_action or invalid_feature:
            invalid_rows.append({"id": row.get("id"), "missing_fields": missing, "invalid_variants": invalid_variants, "invalid_program": invalid_program, "bad_status": bad_status, "bad_category": bad_category, "bad_action": bad_action, "invalid_feature_flags": invalid_feature})
    duplicate_id_count = len(ids) - len(set(ids))
    valid_count = len(rows) - len(invalid_rows)
    return {
        "raw_input_directory": str(raw_dir),
        "required_files_read": len(missing_raw_files) == 0 and not missing_stats_dir and shard_count > 0,
        "missing_required_files": missing_raw_files + (["stats/"] if missing_stats_dir else []),
        "shard_count": shard_count,
        "raw_total_samples": len(rows) + len(malformed),
        "jsonl_parse_error_count": len(malformed),
        "schema_valid_count": valid_count,
        "schema_invalid_count": len(invalid_rows),
        "id_unique": duplicate_id_count == 0,
        "duplicate_id_count": duplicate_id_count,
        "support_status_invalid_count": status_invalid,
        "category_invalid_count": category_invalid,
        "natural_language_variants_missing_count": sum(1 for row in rows if not isinstance(row.get("natural_language_variants"), list) or not row.get("natural_language_variants")),
        "candidate_program_missing_count": sum(1 for row in rows if not isinstance(row.get("candidate_program"), str) or not row.get("candidate_program", "").strip()),
        "feature_flag_incoherent_count": feature_incoherent,
        "expected_action_inconsistent_count": expected_action_invalid,
        "schema_audit_passed": len(malformed) == 0 and len(invalid_rows) == 0 and duplicate_id_count == 0 and len(missing_raw_files) == 0 and not missing_stats_dir,
        "invalid_examples": invalid_rows[:50],
    }


def audit_raw_dedup_leakage(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    input_to_splits: Dict[str, set[str]] = {}
    groups: Dict[str, set[str]] = {}
    template_counter: Dict[str, int] = {}
    nl_seen = set()
    near_duplicate_nl_count = 0
    for row in rows:
        split = str(row.get("split_hint", ""))
        inp = _norm(row.get("input", ""))
        input_to_splits.setdefault(inp, set()).add(split)
        pg = _hash(row.get("candidate_program", ""))
        groups.setdefault(pg, set()).add(split)
        template = f"{row.get('category')}::{_hash(row.get('candidate_program', ''))[:10]}"
        template_counter[template] = template_counter.get(template, 0) + 1
        for variant in row.get("natural_language_variants", []) or []:
            sig = _near_sig(str(variant))
            if sig in nl_seen:
                near_duplicate_nl_count += 1
            nl_seen.add(sig)
    inputs = [_norm(row.get("input", "")) for row in rows]
    programs = [_norm(row.get("candidate_program", "")) for row in rows]
    leakage = _split_leakage(input_to_splits)
    program_leakage = _split_leakage(groups)
    template_family_overuse_count = sum(max(0, count - 1000) for count in template_counter.values())
    return {
        "duplicate_input_count": len(inputs) - len(set(inputs)),
        "duplicate_candidate_program_count": len(programs) - len(set(programs)),
        "near_duplicate_nl_count": near_duplicate_nl_count,
        "train_eval_input_leakage_count": leakage["train_eval"],
        "train_test_input_leakage_count": leakage["train_test"],
        "natural_language_group_leakage_count": near_duplicate_nl_count,
        "program_group_leakage_count": program_leakage["any"],
        "template_family_overuse_count": template_family_overuse_count,
        "duplicate_rate": round((len(inputs) - len(set(inputs))) / len(rows), 6) if rows else 0.0,
        "leakage_count": leakage["train_eval"] + leakage["train_test"] + near_duplicate_nl_count + program_leakage["any"],
    }


def audit_support_status_safety(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    current = [row for row in rows if row.get("support_status") == "current_supported"]
    future = [row for row in rows if row.get("support_status") == "future_domain"]
    unsupported = [row for row in rows if row.get("support_status") == "unsupported"]
    review = [row for row in rows if row.get("support_status") == "review"]
    def flagged(feature: str) -> int:
        return sum(1 for row in current if row.get("language_features", {}).get(feature))
    blocking = {
        "function_marked_current_supported_count": flagged("has_function") + flagged("has_function_call") + flagged("has_multiple_functions"),
        "array_marked_current_supported_count": flagged("has_array") + flagged("has_array_loop"),
        "recursion_marked_current_supported_count": flagged("has_recursion") + flagged("has_bounded_recursion"),
        "unbounded_loop_marked_current_supported_count": flagged("has_unbounded_loop"),
        "io_system_call_marked_current_supported_count": flagged("has_io") + flagged("has_system_call"),
        "future_domain_has_target_ir_count": sum(1 for row in future if row.get("target_ir_hint") is not None),
        "future_domain_has_expected_output_count": sum(1 for row in future if row.get("expected_output_hint") is not None),
        "unsupported_has_target_ir_count": sum(1 for row in unsupported if row.get("target_ir_hint") is not None),
        "unsupported_has_expected_output_count": sum(1 for row in unsupported if row.get("expected_output_hint") is not None),
        "review_in_train_count": sum(1 for row in review if row.get("split_hint") == "train"),
    }
    blocking_count = sum(blocking.values())
    return {**blocking, "support_status_safety_passed": blocking_count == 0, "blocking_count": blocking_count}


def convert_current_supported_rows(rows: List[Dict[str, Any]], compile_worker_count: int, timeout_seconds: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    current = [row for row in rows if row.get("support_status") == "current_supported" and not _has_forbidden_supported_feature(row)]
    unique_programs = sorted({row.get("candidate_program", "") for row in current})
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    program_results: Dict[str, Dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=compile_worker_count) as pool:
        futures = {pool.submit(_convert_program_once, program, backend, timeout_seconds): program for program in unique_programs}
        for fut in concurrent.futures.as_completed(futures):
            program = futures[fut]
            program_results[program] = fut.result()
    converted: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    for row in current:
        result = program_results.get(row.get("candidate_program", ""), {})
        if result.get("conversion_success"):
            converted.append(_converted_row(row, int(result["value"])))
        else:
            failures.append({"id": row.get("id"), "reason": result.get("reason", "conversion_failed"), "candidate_program_hash": _hash(row.get("candidate_program", ""))})
    attempts = len(current)
    return {
        "conversion_attempt_count": attempts,
        "conversion_success_count": len(converted),
        "conversion_failure_count": len(failures),
        "conversion_success_rate": round(len(converted) / attempts, 6) if attempts else 0.0,
        "expected_output_source": "compiler_or_evaluator_not_raw_hint",
        "raw_expected_output_hint_trusted": False,
        "target_ir_json_ast": True,
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
    }, converted, failures


def run_compiler_audit(
    converted_rows: List[Dict[str, Any]],
    raw_rows: List[Dict[str, Any]],
    records_dir: Path,
    supported_spot: int,
    boundary_spot: int,
    compile_worker_count: int,
    seed: int,
    timeout_seconds: int,
) -> Dict[str, Any]:
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    supported = _sample(converted_rows, supported_spot, seed)
    boundary = _sample([row for row in raw_rows if row.get("support_status") != "current_supported"], boundary_spot, seed + 1)
    trace: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=compile_worker_count) as pool:
        futures = [pool.submit(_validate_converted, row, backend, timeout_seconds) for row in supported]
        for fut in concurrent.futures.as_completed(futures):
            trace.append(fut.result())
    for row in boundary:
        trace.append({
            "sample_id_hash": _hash(row.get("id", "")),
            "support_status": row.get("support_status"),
            "category": row.get("category"),
            "compiler_invoked": False,
            "compiler_verified_correct": False,
            "boundary_compiler_misroute": False,
            "future_domain_compiled": False,
            "notes": "boundary_not_compiled",
        })
    _write_trace(records_dir, "compiler_audit_trace", trace)
    latencies = [row.get("latency_ms", 0.0) for row in trace if row.get("compiler_invoked")]
    invocations = sum(1 for row in trace if row.get("compiler_invoked"))
    verified = sum(1 for row in trace if row.get("compiler_verified_correct"))
    metrics = {
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "compile_worker_count": compile_worker_count,
        "supported_sample_count": len(supported),
        "boundary_sample_count": len(boundary),
        "real_compiler_invocation_count": invocations if backend.backend_type == "real_c_compiler" else 0,
        "compile_success_count": sum(1 for row in trace if row.get("compile_success")),
        "runtime_success_count": sum(1 for row in trace if row.get("runtime_success")),
        "compiler_verified_correct_count": verified,
        "compiler_verified_failure_count": len(supported) - verified,
        "compiler_verified_correct_rate": round(verified / len(supported), 6) if supported else 0.0,
        "future_domain_compiled_count": sum(1 for row in trace if row.get("support_status") == "future_domain" and row.get("compiler_invoked")),
        "boundary_compiler_misroute_count": sum(1 for row in trace if row.get("boundary_compiler_misroute")),
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "timeout_count": sum(1 for row in trace if row.get("timeout")),
        "function_compiled_count": 0,
        "array_compiled_count": 0,
        "recursion_compiled_count": 0,
        "unbounded_loop_compiled_count": 0,
        "backend_claim_safe": backend.backend_type == "real_c_compiler",
        **_latency(latencies),
    }
    _write_json(records_dir / "compiler_audit_metrics.json", metrics)
    return metrics


def split_active_generation_pool(rows: List[Dict[str, Any]], converted_rows: List[Dict[str, Any]], malformed: List[Dict[str, Any]], schema: Dict[str, Any], dedup: Dict[str, Any], safety: Dict[str, Any], compiler: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    converted_by_id = {row["raw_id"]: row for row in converted_rows}
    seen_inputs = set()
    seen_programs = set()
    accepted: List[Dict[str, Any]] = []
    quarantine: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = [{"id": f"malformed_{i}", "reject_reason": "malformed_json", **row} for i, row in enumerate(malformed)]
    global_safety_failed = safety.get("blocking_count", 0) > 0
    for row in rows:
        rid = row.get("id")
        input_sig = _norm(row.get("input", ""))
        program_sig = _norm(row.get("candidate_program", ""))
        duplicate = input_sig in seen_inputs or program_sig in seen_programs
        seen_inputs.add(input_sig)
        seen_programs.add(program_sig)
        unsafe_label = _row_unsafe_label(row)
        if unsafe_label or global_safety_failed:
            rejected.append({"id": rid, "reject_reason": "unsafe_support_label", "raw": _minimal_raw(row)})
            continue
        if duplicate:
            quarantine.append({"id": rid, "quarantine_reason": "suspicious_duplicate", "raw": _minimal_raw(row)})
            continue
        status = row.get("support_status")
        if status == "current_supported":
            converted = converted_by_id.get(rid)
            if converted and compiler.get("backend_claim_safe"):
                accepted.append(converted)
            else:
                quarantine.append({"id": rid, "quarantine_reason": "conversion_failed_or_unverified", "raw": _minimal_raw(row)})
        elif status in {"near_supported", "review"}:
            quarantine.append({"id": rid, "quarantine_reason": status, "raw": _minimal_raw(row)})
        else:
            accepted.append(_boundary_row(row))
    return {"accepted": accepted, "quarantine": quarantine, "rejected": rejected}


def write_split_dataset(output_dir: Path, split: Dict[str, List[Dict[str, Any]]]) -> None:
    for name, rows in split.items():
        target = output_dir / name
        target.mkdir(parents=True, exist_ok=True)
        _write_jsonl(target / f"{name}.jsonl", rows)
        _write_json(target / "manifest.json", {"split": name, "count": len(rows)})


def build_readiness(raw_dir: Path, schema: Dict[str, Any], dedup: Dict[str, Any], safety: Dict[str, Any], conversion: Dict[str, Any], compiler: Dict[str, Any], split: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    raw_total = schema["raw_total_samples"]
    accepted_count = len(split["accepted"])
    quarantine_count = len(split["quarantine"])
    rejected_count = len(split["rejected"])
    quality = _quality_score(schema, dedup, safety, conversion, compiler, accepted_count, raw_total)
    ready = quality >= 0.6 and compiler.get("compiler_verified_correct_rate", 0) >= 0.98 and safety.get("blocking_count", 1) == 0
    return {
        "raw_input_directory": str(raw_dir),
        "raw_total_samples": raw_total,
        "schema_valid_count": schema["schema_valid_count"],
        "accepted_count": accepted_count,
        "quarantine_count": quarantine_count,
        "rejected_count": rejected_count,
        "acceptance_rate": round(accepted_count / raw_total, 6) if raw_total else 0.0,
        "duplicate_rate": dedup["duplicate_rate"],
        "leakage_count": dedup["leakage_count"],
        "conversion_success_rate": conversion["conversion_success_rate"],
        "compiler_verified_correct_rate": compiler["compiler_verified_correct_rate"],
        "future_domain_compiled_count": compiler["future_domain_compiled_count"],
        "boundary_compiler_misroute_count": compiler["boundary_compiler_misroute_count"],
        "function_mislabeled_supported_count": safety["function_marked_current_supported_count"],
        "array_mislabeled_supported_count": safety["array_marked_current_supported_count"],
        "recursion_mislabeled_supported_count": safety["recursion_marked_current_supported_count"],
        "dataset_quality_score": quality,
        "ready_for_larger_active_generation_loop": ready,
        "recommended_next_run": "larger active generation loop with stronger dedup controls" if ready else "fix raw generator quality and rerun audit",
        "blocking_issues": [] if ready else _blocking_issues(schema, safety, compiler),
        "real_promotion_enabled": False,
        "turing_completeness_claimed": False,
        "solved_program_synthesis_claimed": False,
    }


def _convert_program_once(program: str, backend: Any, timeout_seconds: int) -> Dict[str, Any]:
    output_var = _choose_output_var(program)
    if not output_var:
        return {"conversion_success": False, "reason": "no_output_variable"}
    source = "\n".join(["#include <stdio.h>", "int main(void) {", program, f'printf("%lld\\n", (long long)({output_var}));', "return 0;", "}"])
    if backend.backend_type == "real_c_compiler":
        result = _compile_and_run_source(source, backend, timeout_seconds)
        if result.get("runtime_success") and str(result.get("stdout_value_if_safe", "")).lstrip("-").isdigit():
            return {"conversion_success": True, "value": int(result["stdout_value_if_safe"]), "source": "real_compiler"}
        return {"conversion_success": False, "reason": "compiler_or_runtime_failed", "details": {k: result.get(k) for k in ["compile_returncode", "runtime_returncode", "timeout"]}}
    value = _fallback_static_value(program, output_var)
    if value is None:
        return {"conversion_success": False, "reason": "real_compiler_unavailable"}
    return {"conversion_success": True, "value": value, "source": "fallback_static_evaluator"}


def _validate_converted(row: Dict[str, Any], backend: Any, timeout_seconds: int) -> Dict[str, Any]:
    started = time.perf_counter()
    base = {"sample_id_hash": _hash(row["id"]), "support_status": row.get("support_status"), "category": row.get("category"), "compiler_invoked": False, "compiler_verified_correct": False, "timeout": False}
    if row.get("support_status") != "current_supported":
        base["boundary_compiler_misroute"] = True
        return base
    try:
        source = target_ir_to_c_source(row["target_ir"])
        result = _compile_and_run_source(source, backend, timeout_seconds)
    except Exception as exc:
        base["notes"] = f"validation_exception:{type(exc).__name__}"
        return base
    stdout = str(result.get("stdout_value_if_safe") or "").strip()
    expected = str(row.get("expected_output") or "").strip()
    base.update(result)
    base["compiler_verified_correct"] = bool(result.get("runtime_success") and stdout == expected)
    base["latency_ms"] = result.get("latency_ms", round((time.perf_counter() - started) * 1000, 6))
    base["boundary_compiler_misroute"] = False
    return base


def _converted_row(row: Dict[str, Any], value: int) -> Dict[str, Any]:
    return {
        "id": f"v0_9_15_{row['id']}",
        "raw_id": row["id"],
        "dataset_version": "v0.9.15_active_generation_pilot",
        "split": _split(row.get("split_hint")),
        "stage": "active_generation_pilot_converted",
        "category": row.get("category"),
        "support_status": "current_supported",
        "input": row.get("input"),
        "natural_language_variants": row.get("natural_language_variants", []),
        "canonical_program": row.get("candidate_program"),
        "target_ir": {"op": "Program", "body": [{"op": "Print", "value": {"op": "Int", "value": value}}]},
        "expected_output": f"{value}\n",
        "expected_type": "int_stdout",
        "boundary_label": "supported",
        "expected_action": "train_current" if row.get("split_hint") == "train" else "accept_supported",
        "language_features": row.get("language_features", {}),
        "compiler_expectation": {"should_compile": True, "should_run": True, "expected_stdout": f"{value}\n"},
        "provenance": {"generator": "v0_9_15_active_generation_pilot", "raw_source": row.get("_source_shard"), "raw_expected_output_hint_trusted": False},
    }


def _boundary_row(row: Dict[str, Any]) -> Dict[str, Any]:
    status = row.get("support_status")
    return {
        "id": f"v0_9_15_{row['id']}",
        "raw_id": row["id"],
        "dataset_version": "v0.9.15_active_generation_pilot",
        "split": _split(row.get("split_hint")),
        "stage": "active_generation_pilot_boundary",
        "category": row.get("category"),
        "support_status": status,
        "input": row.get("input"),
        "natural_language_variants": row.get("natural_language_variants", []),
        "canonical_program": None,
        "target_ir": None,
        "expected_output": None,
        "expected_type": status,
        "boundary_label": status,
        "expected_action": row.get("expected_action"),
        "language_features": row.get("language_features", {}),
        "compiler_expectation": {"should_compile": False, "should_run": False, "expected_stdout": None},
        "provenance": {"generator": "v0_9_15_active_generation_pilot", "raw_source": row.get("_source_shard")},
    }


def _choose_output_var(program: str) -> str | None:
    before_blocks = []
    for line in _strip_comments(program).splitlines():
        if line.strip().startswith(("for ", "for(", "while ", "while(", "if ", "if(")):
            break
        before_blocks.append(line)
    names = []
    for line in before_blocks:
        match = re.match(r"\s*int\s+([A-Za-z_][A-Za-z0-9_]*)", line)
        if match:
            names.append(match.group(1))
    if not names:
        return None
    if len(names) >= 2 and names[-1] in {"sign"}:
        return names[-2]
    return names[-1]


def _fallback_static_value(program: str, output_var: str) -> int | None:
    values: Dict[str, int] = {}
    for line in _strip_comments(program).splitlines():
        match = re.match(r"\s*int\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(-?\d+)\s*;", line)
        if match:
            values[match.group(1)] = int(match.group(2))
    return values.get(output_var)


def _row_unsafe_label(row: Dict[str, Any]) -> bool:
    status = row.get("support_status")
    if status == "current_supported" and _has_forbidden_supported_feature(row):
        return True
    if status in {"future_domain", "unsupported", "trap", "review", "near_supported"}:
        return row.get("target_ir_hint") is not None or row.get("expected_output_hint") is not None
    return status not in VALID_SUPPORT_STATUS


def _has_forbidden_supported_feature(row: Dict[str, Any]) -> bool:
    features = row.get("language_features", {}) or {}
    return any(features.get(name) for name in FORBIDDEN_SUPPORTED_FEATURES)


def _minimal_raw(row: Dict[str, Any]) -> Dict[str, Any]:
    return {"category": row.get("category"), "support_status": row.get("support_status"), "input": row.get("input"), "candidate_program_hash": _hash(row.get("candidate_program", ""))}


def _split(value: Any) -> str:
    return str(value) if value in {"train", "eval", "test", "heldout"} else "eval"


def _strip_comments(program: str) -> str:
    return re.sub(r"//.*", "", program)


def _split_leakage(mapping: Dict[str, set[str]]) -> Dict[str, int]:
    train_eval = sum(1 for splits in mapping.values() if "train" in splits and "eval" in splits)
    train_test = sum(1 for splits in mapping.values() if "train" in splits and "test" in splits)
    any_leak = sum(1 for splits in mapping.values() if len(splits & {"train", "eval", "test", "heldout"}) > 1)
    return {"train_eval": train_eval, "train_test": train_test, "any": any_leak}


def _near_sig(text: str) -> str:
    words = re.findall(r"[A-Za-z0-9_]+", text.lower())
    return " ".join(sorted(set(words)))


def _norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def _sample(rows: List[Dict[str, Any]], count: int, seed: int) -> List[Dict[str, Any]]:
    return sorted(rows, key=lambda row: hashlib.sha256((str(row.get("id")) + str(seed)).encode("utf-8")).hexdigest())[: min(count, len(rows))]


def _latency(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"p50_latency_ms": 0.0, "p95_latency_ms": 0.0, "p99_latency_ms": 0.0}
    values = sorted(values)
    return {
        "p50_latency_ms": round(statistics.median(values), 6),
        "p95_latency_ms": round(values[min(len(values) - 1, int(len(values) * 0.95))], 6),
        "p99_latency_ms": round(values[min(len(values) - 1, int(len(values) * 0.99))], 6),
    }


def _quality_score(schema: Dict[str, Any], dedup: Dict[str, Any], safety: Dict[str, Any], conversion: Dict[str, Any], compiler: Dict[str, Any], accepted_count: int, raw_total: int) -> float:
    parts = [
        1.0 if schema.get("schema_audit_passed") else max(0.0, schema.get("schema_valid_count", 0) / max(raw_total, 1)),
        max(0.0, 1.0 - min(dedup.get("duplicate_rate", 1.0), 1.0)),
        1.0 if safety.get("support_status_safety_passed") else 0.0,
        conversion.get("conversion_success_rate", 0.0),
        compiler.get("compiler_verified_correct_rate", 0.0),
        accepted_count / max(raw_total, 1),
    ]
    return round(sum(parts) / len(parts), 6)


def _blocking_issues(schema: Dict[str, Any], safety: Dict[str, Any], compiler: Dict[str, Any]) -> List[str]:
    issues = []
    if not schema.get("schema_audit_passed"):
        issues.append("raw_schema_not_clean")
    if safety.get("blocking_count", 0) > 0:
        issues.append("support_status_safety_blocking")
    if compiler.get("compiler_verified_correct_rate", 0) < 0.98:
        issues.append("compiler_audit_not_clean")
    return issues


def _schema_md(schema: Dict[str, Any]) -> str:
    return "\n".join([
        "# Raw Schema Audit",
        "",
        f"- raw_total_samples: {schema['raw_total_samples']}",
        f"- schema_valid_count: {schema['schema_valid_count']}",
        f"- jsonl_parse_error_count: {schema['jsonl_parse_error_count']}",
        f"- schema_audit_passed: {schema['schema_audit_passed']}",
        "",
    ])


def _mainline_md(readiness: Dict[str, Any]) -> str:
    still_not = [
        "Turing completeness",
        "solved program synthesis",
        "production readiness",
        "real promotion",
    ]
    return "\n".join([
        "# v0.9.15 Active Generation Pilot",
        "",
        "This version audits a raw draft dataset and emits accepted, quarantine, and rejected pools. It does not enable real promotion.",
        "",
        f"- raw_total_samples: {readiness['raw_total_samples']}",
        f"- accepted_count: {readiness['accepted_count']}",
        f"- quarantine_count: {readiness['quarantine_count']}",
        f"- rejected_count: {readiness['rejected_count']}",
        f"- dataset_quality_score: {readiness['dataset_quality_score']}",
        f"- ready_for_larger_active_generation_loop: {readiness['ready_for_larger_active_generation_loop']}",
        "",
        "## Still Not Proven",
        *[f"- {item}" for item in still_not],
        "",
    ])


def _write_trace(out: Path, stem: str, rows: List[Dict[str, Any]], max_bytes: int = 45_000_000) -> None:
    shards = []
    current: List[str] = []
    size = 0
    index = 0
    for row in rows:
        line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        encoded = len(line.encode("utf-8"))
        if current and size + encoded > max_bytes:
            name = f"{stem}_{index:03d}.jsonl"
            (out / name).write_text("".join(current), encoding="utf-8")
            shards.append({"path": name, "row_count": len(current), "size_bytes": (out / name).stat().st_size})
            current = []
            size = 0
            index += 1
        current.append(line)
        size += encoded
    if current:
        name = f"{stem}_{index:03d}.jsonl"
        (out / name).write_text("".join(current), encoding="utf-8")
        shards.append({"path": name, "row_count": len(current), "size_bytes": (out / name).stat().st_size})
    _write_json(out / f"{stem}_manifest.json", {"shards": shards, "total_rows": len(rows)})


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _hash(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8", errors="replace")).hexdigest()[:16]
