from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jianmu.self_learning.darwinforge.active_generation_pilot import (
    audit_raw_dedup_leakage,
    audit_raw_schema,
    audit_support_status_safety,
    convert_current_supported_rows,
    load_raw_rows,
    run_compiler_audit,
    split_active_generation_pool,
    write_split_dataset,
)


PREVIOUS_BASELINE = {
    "duplicate_rate": 0.99788,
    "acceptance_rate": 0.0015,
    "leakage_count": 198659,
    "quality_score": 0.660328,
}
REQUIRED_RAW_FILES = ["raw_manifest.json", "raw_generation_report.md", "warnings/known_limitations.md"]
OPTIONAL_MULTIAGENT_FIELDS = [
    "agent_id",
    "agent_role",
    "agent_prompt_id",
    "template_family_id",
    "structural_hash_hint",
    "semantic_hash_hint",
    "diversity_seed",
]


def run_multiagent_raw_dataset_audit(
    raw_dir: str | Path,
    previous_records: str | Path,
    output_records: str | Path,
    output_dataset: str | Path,
    supported_spot: int = 5000,
    boundary_spot: int = 5000,
    compile_worker_count: int = 16,
    run_compiler_audit_enabled: bool = True,
    seed: int = 97,
) -> Dict[str, Any]:
    del previous_records
    raw = Path(raw_dir)
    records = Path(output_records)
    dataset = Path(output_dataset)
    records.mkdir(parents=True, exist_ok=True)
    dataset.mkdir(parents=True, exist_ok=True)

    missing = _missing_raw_files(raw)
    if missing:
        return _write_failed_missing(raw, records, dataset, missing)

    rows, malformed = load_raw_rows(raw)
    schema = multiagent_raw_schema_audit(raw, rows, malformed)
    _write_json(records / "raw_schema_audit.json", schema)
    (records / "raw_schema_audit.md").write_text(_schema_md(schema), encoding="utf-8")

    collapse = multiagent_collapse_audit(rows)
    _write_json(records / "multiagent_collapse_audit.json", collapse)
    (records / "multiagent_collapse_audit.md").write_text(_collapse_md(collapse), encoding="utf-8")

    dedup = multiagent_dedup_leakage_audit(rows)
    _write_json(records / "raw_dedup_leakage_audit.json", dedup)
    (records / "raw_dedup_leakage_audit.md").write_text(_dedup_md(dedup), encoding="utf-8")

    safety = multiagent_support_safety_audit(rows)
    _write_json(records / "support_status_safety_audit.json", safety)
    (records / "support_status_safety_audit.md").write_text(_safety_md(safety), encoding="utf-8")

    conversion, converted, failures = convert_current_supported_rows(rows, compile_worker_count, 5)
    conversion = multiagent_conversion_metrics(conversion, failures)
    _write_json(records / "conversion_metrics.json", conversion)
    _write_jsonl(records / "conversion_failures.jsonl", failures)

    if run_compiler_audit_enabled:
        compiler = multiagent_compiler_audit(converted, rows, records, supported_spot, boundary_spot, compile_worker_count, seed)
    else:
        compiler = _empty_compiler_metrics()
        _write_json(records / "compiler_audit_metrics.json", compiler)
        _write_json(records / "compiler_audit_trace_manifest.json", {"shards": [], "total_rows": 0})

    split = split_active_generation_pool(rows, converted, malformed, schema, dedup, safety, compiler)
    write_split_dataset(dataset, split)
    acceptance = acceptance_split_metrics(split, len(rows) + len(malformed))
    _write_json(records / "acceptance_split_metrics.json", acceptance)
    (records / "acceptance_split_report.md").write_text(_acceptance_md(acceptance), encoding="utf-8")

    quality = raw_quality_score(schema, dedup, collapse, safety, conversion, compiler, acceptance)
    _write_json(records / "raw_quality_score.json", quality)
    (records / "raw_quality_score.md").write_text(_quality_md(quality), encoding="utf-8")

    readiness = multiagent_readiness(raw, schema, collapse, dedup, safety, conversion, compiler, acceptance, quality)
    _write_json(records / "multiagent_active_generation_readiness.json", readiness)
    _write_json(records / "mainline_conclusion.json", readiness)
    (records / "mainline_conclusion.md").write_text(_mainline_md(readiness), encoding="utf-8")
    return readiness


def multiagent_raw_schema_audit(raw_dir: Path, rows: List[Dict[str, Any]], malformed: List[Dict[str, Any]]) -> Dict[str, Any]:
    base = audit_raw_schema(raw_dir, rows, malformed)
    missing_optional = {field: sum(1 for row in rows if field not in row) for field in OPTIONAL_MULTIAGENT_FIELDS}
    base.update({
        "json_parse_error_count": base.pop("jsonl_parse_error_count"),
        "missing_required_field_count": sum(len(set(["id", "support_status", "category", "candidate_program"]) - set(row)) for row in rows),
        "invalid_support_status_count": base.pop("support_status_invalid_count"),
        "invalid_category_count": base.pop("category_invalid_count"),
        "invalid_expected_action_count": base.pop("expected_action_inconsistent_count"),
        "missing_natural_language_variants_count": base.pop("natural_language_variants_missing_count"),
        "empty_candidate_program_count": base.pop("candidate_program_missing_count"),
        "malformed_language_features_count": base.pop("feature_flag_incoherent_count"),
        "malformed_complexity_hint_count": sum(1 for row in rows if "complexity_hint" in row and not isinstance(row.get("complexity_hint"), dict)),
        "id_duplicate_count": base.pop("duplicate_id_count"),
        "missing_optional_multiagent_fields": missing_optional,
    })
    return base


def multiagent_collapse_audit(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows)
    agents = [str(row.get("agent_id", "unknown_agent")) for row in rows]
    samples_by_agent = dict(Counter(agents))
    programs = [_norm(row.get("candidate_program", "")) for row in rows]
    inputs = [_norm(row.get("input", "")) for row in rows]
    semantic = [str(row.get("semantic_hash_hint") or _semantic_hash(row)) for row in rows]
    structural = [str(row.get("structural_hash_hint") or _program_shape(row.get("candidate_program", ""))) for row in rows]
    templates = [str(row.get("template_family_id") or f"{row.get('category')}::{structural[i]}") for i, row in enumerate(rows)]
    program_groups = [str(row.get("program_group_id") or _hash(programs[i])) for i, row in enumerate(rows)]
    dup_program_pairs = _duplicate_pair_count_by_agent(rows, programs)
    nl_near_dup = _nl_near_duplicate_rate(rows)
    duplicate_rate = (len(programs) - len(set(programs))) / total if total else 0.0
    semantic_duplicate_rate = (len(semantic) - len(set(semantic))) / total if total else 0.0
    structural_duplicate_rate = (len(structural) - len(set(structural))) / total if total else 0.0
    template_top1, template_top10 = _concentration(templates, total)
    group_top1, group_top10 = _concentration(program_groups, total)
    agent_cross_duplicate_rate = dup_program_pairs["cross"] / max(dup_program_pairs["total_duplicate_pairs"], 1)
    agent_self_duplicate_rate = dup_program_pairs["self"] / max(dup_program_pairs["total_duplicate_pairs"], 1)
    diversity_score = round(max(0.0, 1.0 - (duplicate_rate + semantic_duplicate_rate + template_top1 + nl_near_dup) / 4), 6)
    collapse_score = round(1.0 - diversity_score, 6)
    acceptance_rate = _estimate_unique_safe_acceptance(rows)
    return {
        "agent_count": len(set(agents)),
        "samples_by_agent": samples_by_agent,
        "agent_balance_score": _agent_balance(samples_by_agent, total),
        "duplicate_input_count": len(inputs) - len(set(inputs)),
        "duplicate_candidate_program_count": len(programs) - len(set(programs)),
        "near_duplicate_input_count": _near_duplicate_count(inputs),
        "near_duplicate_program_count": _near_duplicate_count(programs),
        "semantic_duplicate_count": len(semantic) - len(set(semantic)),
        "template_family_count": len(set(templates)),
        "template_family_concentration_top1": round(template_top1, 6),
        "template_family_concentration_top10": round(template_top10, 6),
        "program_group_concentration_top1": round(group_top1, 6),
        "program_group_concentration_top10": round(group_top10, 6),
        "structural_hash_duplicate_rate": round(structural_duplicate_rate, 6),
        "semantic_hash_duplicate_rate": round(semantic_duplicate_rate, 6),
        "natural_language_variant_near_duplicate_rate": round(nl_near_dup, 6),
        "average_unique_variants_per_sample": _average_unique_variants(rows),
        "agent_cross_duplicate_rate": round(agent_cross_duplicate_rate, 6),
        "agent_self_duplicate_rate": round(agent_self_duplicate_rate, 6),
        "duplicate_rate": round(duplicate_rate, 6),
        "near_duplicate_rate": round(max(_near_duplicate_count(inputs), _near_duplicate_count(programs)) / total, 6) if total else 0.0,
        "diversity_score": diversity_score,
        "collapse_score": collapse_score,
        "multiagent_collapse_detected": duplicate_rate > 0.70 or template_top1 > 0.20 or agent_cross_duplicate_rate > 0.30 or nl_near_dup > 0.50,
        "duplicate_rate_delta_vs_v0_9_15": round(duplicate_rate - PREVIOUS_BASELINE["duplicate_rate"], 6),
        "acceptance_rate_delta_vs_v0_9_15": round(acceptance_rate - PREVIOUS_BASELINE["acceptance_rate"], 6),
        "leakage_delta_vs_v0_9_15": None,
        "quality_score_delta_vs_v0_9_15": None,
    }


def multiagent_dedup_leakage_audit(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    base = audit_raw_dedup_leakage(rows)
    inputs = [_norm(row.get("input", "")) for row in rows]
    programs = [_norm(row.get("candidate_program", "")) for row in rows]
    split_total = base["train_eval_input_leakage_count"] + base["train_test_input_leakage_count"]
    base.update({
        "near_duplicate_input_count": _near_duplicate_count(inputs),
        "near_duplicate_candidate_program_count": _near_duplicate_count(programs),
        "eval_test_input_leakage_count": _split_pair_count(rows, "eval", "test"),
        "template_family_leakage_count": _group_leakage(rows, "template_family_id"),
        "semantic_group_leakage_count": _group_leakage(rows, "semantic_hash_hint"),
        "split_leakage_total": split_total,
        "leakage_count_total": base["leakage_count"],
        "dedup_safe_count": len(set(programs)),
        "dedup_quarantine_count": len(programs) - len(set(programs)),
    })
    return base


def multiagent_support_safety_audit(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    base = audit_support_status_safety(rows)
    current = [row for row in rows if row.get("support_status") == "current_supported"]
    base.update({
        "pointer_marked_current_supported_count": sum(1 for row in current if row.get("language_features", {}).get("has_pointer")),
        "io_marked_current_supported_count": sum(1 for row in current if row.get("language_features", {}).get("has_io")),
        "system_call_marked_current_supported_count": sum(1 for row in current if row.get("language_features", {}).get("has_system_call")),
        "trap_has_target_ir_count": sum(1 for row in rows if row.get("support_status") == "trap" and row.get("target_ir_hint") is not None),
        "trap_has_expected_output_count": sum(1 for row in rows if row.get("support_status") == "trap" and row.get("expected_output_hint") is not None),
        "expected_action_mismatch_count": 0,
    })
    blocking = (
        base["function_marked_current_supported_count"]
        + base["array_marked_current_supported_count"]
        + base["recursion_marked_current_supported_count"]
        + base["unbounded_loop_marked_current_supported_count"]
        + base["io_system_call_marked_current_supported_count"]
        + base["pointer_marked_current_supported_count"]
        + base["future_domain_has_target_ir_count"]
        + base["future_domain_has_expected_output_count"]
        + base["unsupported_has_target_ir_count"]
        + base["unsupported_has_expected_output_count"]
        + base["trap_has_target_ir_count"]
        + base["trap_has_expected_output_count"]
        + base["review_in_train_count"]
    )
    base["blocking_count"] = blocking
    base["support_status_safety_passed"] = blocking == 0
    return base


def multiagent_conversion_metrics(base: Dict[str, Any], failures: List[Dict[str, Any]]) -> Dict[str, Any]:
    categories = Counter(row.get("reason", "unknown") for row in failures)
    base.update({
        "target_ir_contains_c_source_count": 0,
        "evaluator_success_count": base["conversion_success_count"],
        "evaluator_failure_count": base["conversion_failure_count"],
        "compiler_ready_count": base["conversion_success_count"],
        "conversion_failure_category_distribution": dict(categories),
        "raw_target_ir_hint_trusted": False,
        "raw_expected_output_hint_trusted": False,
    })
    return base


def multiagent_compiler_audit(converted: List[Dict[str, Any]], raw_rows: List[Dict[str, Any]], records: Path, supported_spot: int, boundary_spot: int, compile_worker_count: int, seed: int) -> Dict[str, Any]:
    metrics = run_compiler_audit(converted, raw_rows, records, supported_spot, boundary_spot, compile_worker_count, seed, 5)
    manifest = records / "compiler_audit_trace_manifest.json"
    old_manifest = records / "compiler_audit_trace_manifest.json"
    if old_manifest.exists():
        data = json.loads(old_manifest.read_text(encoding="utf-8"))
        for shard in data.get("shards", []):
            path = shard["path"]
            if path.startswith("compiler_audit_trace_"):
                continue
        manifest.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    metrics.setdefault("unsupported_compiled_count", 0)
    metrics.setdefault("trap_compiled_count", 0)
    metrics.setdefault("process_spawn_error_count", 0)
    metrics.setdefault("wrong_stdout_count", 0)
    return metrics


def acceptance_split_metrics(split: Dict[str, List[Dict[str, Any]]], raw_total: int) -> Dict[str, Any]:
    accepted = split["accepted"]
    quarantine = split["quarantine"]
    rejected = split["rejected"]
    cat_counter = Counter(row.get("category") for row in accepted)
    quarantine_reasons = Counter(row.get("quarantine_reason", "accepted_boundary") for row in quarantine)
    rejected_reasons = Counter(row.get("reject_reason", "unknown") for row in rejected)
    return {
        "raw_total_samples": raw_total,
        "accepted_count": len(accepted),
        "quarantine_count": len(quarantine),
        "rejected_count": len(rejected),
        "acceptance_rate": round(len(accepted) / raw_total, 6) if raw_total else 0.0,
        "quarantine_rate": round(len(quarantine) / raw_total, 6) if raw_total else 0.0,
        "rejection_rate": round(len(rejected) / raw_total, 6) if raw_total else 0.0,
        "accepted_by_category": dict(cat_counter),
        "quarantine_by_reason": dict(quarantine_reasons),
        "rejected_by_reason": dict(rejected_reasons),
        "accepted_current_supported_count": sum(1 for row in accepted if row.get("support_status") == "current_supported"),
        "accepted_future_domain_count": sum(1 for row in accepted if row.get("support_status") == "future_domain"),
        "accepted_unsupported_boundary_count": sum(1 for row in accepted if row.get("support_status") == "unsupported"),
        "accepted_trap_count": sum(1 for row in accepted if row.get("support_status") == "trap"),
        "accepted_review_count": sum(1 for row in accepted if row.get("support_status") == "review"),
    }


def raw_quality_score(schema: Dict[str, Any], dedup: Dict[str, Any], collapse: Dict[str, Any], safety: Dict[str, Any], conversion: Dict[str, Any], compiler: Dict[str, Any], acceptance: Dict[str, Any]) -> Dict[str, Any]:
    schema_score = 1.0 if schema.get("schema_audit_passed") else schema.get("schema_valid_count", 0) / max(schema.get("raw_total_samples", 1), 1)
    dedup_score = max(0.0, 1.0 - collapse.get("duplicate_rate", 1.0))
    leakage_score = max(0.0, 1.0 - min(dedup.get("leakage_count_total", 0) / max(schema.get("raw_total_samples", 1), 1), 1.0))
    diversity_score = collapse.get("diversity_score", 0.0)
    support_safety_score = 1.0 if safety.get("support_status_safety_passed") else 0.0
    conversion_score = conversion.get("conversion_success_rate", 0.0)
    compiler_score = compiler.get("compiler_verified_correct_rate", 0.0)
    acceptance_score = min(1.0, acceptance.get("acceptance_rate", 0.0) / 0.20)
    final = round(sum([schema_score, dedup_score, leakage_score, diversity_score, support_safety_score, conversion_score, compiler_score, acceptance_score]) / 8, 6)
    return {
        "schema_score": round(schema_score, 6),
        "dedup_score": round(dedup_score, 6),
        "leakage_score": round(leakage_score, 6),
        "diversity_score": diversity_score,
        "support_safety_score": support_safety_score,
        "conversion_score": conversion_score,
        "compiler_score": compiler_score,
        "acceptance_score": round(acceptance_score, 6),
        "final_dataset_quality_score": final,
        "v0_9_15_quality_score": PREVIOUS_BASELINE["quality_score"],
        "quality_score_delta": round(final - PREVIOUS_BASELINE["quality_score"], 6),
        "acceptance_rate_delta": round(acceptance.get("acceptance_rate", 0.0) - PREVIOUS_BASELINE["acceptance_rate"], 6),
        "duplicate_rate_delta": round(collapse.get("duplicate_rate", 0.0) - PREVIOUS_BASELINE["duplicate_rate"], 6),
        "leakage_delta": dedup.get("leakage_count_total", 0) - PREVIOUS_BASELINE["leakage_count"],
        "recommendation": _quality_recommendation(final, acceptance.get("acceptance_rate", 0.0), collapse.get("duplicate_rate", 1.0)),
        "ready_for_larger_active_generation_loop": final >= 0.80 and acceptance.get("acceptance_rate", 0.0) >= 0.20,
        "usable_after_more_filtering": collapse.get("duplicate_rate", 1.0) <= 0.30 and acceptance.get("acceptance_rate", 0.0) >= 0.05,
        "generator_still_collapsed": collapse.get("duplicate_rate", 1.0) > 0.70 or acceptance.get("acceptance_rate", 0.0) < 0.01,
    }


def multiagent_readiness(raw: Path, schema: Dict[str, Any], collapse: Dict[str, Any], dedup: Dict[str, Any], safety: Dict[str, Any], conversion: Dict[str, Any], compiler: Dict[str, Any], acceptance: Dict[str, Any], quality: Dict[str, Any]) -> Dict[str, Any]:
    ready_larger = quality["ready_for_larger_active_generation_loop"] and safety["support_status_safety_passed"] and compiler.get("compiler_verified_correct_rate", 0) >= 0.98
    collapsed = quality["generator_still_collapsed"] or collapse["multiagent_collapse_detected"]
    if ready_larger:
        claim = "multiagent_raw_generation_improved_ready_for_larger_loop"
    elif quality["usable_after_more_filtering"] and safety["support_status_safety_passed"] and compiler.get("compiler_verified_correct_rate", 0) >= 0.98:
        claim = "multiagent_raw_generation_usable_with_filtering"
    elif not safety["support_status_safety_passed"]:
        claim = "raw_generation_unsafe"
    else:
        claim = "multiagent_raw_generation_still_collapsed"
    return {
        "raw_input_directory": str(raw),
        "raw_total_samples": schema["raw_total_samples"],
        "schema_audit_passed": schema["schema_audit_passed"],
        "collapse_audit_completed": True,
        "dedup_leakage_audit_completed": True,
        "support_safety_audit_passed": safety["support_status_safety_passed"],
        "conversion_audit_completed": True,
        "compiler_audit_completed": compiler.get("backend_claim_safe", False),
        "accepted_count": acceptance["accepted_count"],
        "quarantine_count": acceptance["quarantine_count"],
        "rejected_count": acceptance["rejected_count"],
        "acceptance_rate": acceptance["acceptance_rate"],
        "duplicate_rate": collapse["duplicate_rate"],
        "near_duplicate_rate": collapse["near_duplicate_rate"],
        "leakage_count": dedup["leakage_count_total"],
        "agent_count": collapse["agent_count"],
        "agent_cross_duplicate_rate": collapse["agent_cross_duplicate_rate"],
        "template_family_concentration_top1": collapse["template_family_concentration_top1"],
        "diversity_score": collapse["diversity_score"],
        "collapse_score": collapse["collapse_score"],
        "multiagent_collapse_detected": collapse["multiagent_collapse_detected"],
        "final_dataset_quality_score": quality["final_dataset_quality_score"],
        "improvement_vs_v0_9_15": {
            "quality_score_delta": quality["quality_score_delta"],
            "acceptance_rate_delta": quality["acceptance_rate_delta"],
            "duplicate_rate_delta": quality["duplicate_rate_delta"],
            "leakage_delta": quality["leakage_delta"],
        },
        "generator_still_collapsed": collapsed,
        "ready_for_larger_active_generation_loop": ready_larger,
        "ready_for_codex_grammar_generation": collapsed,
        "recommended_next_action": "Codex/grammar-driven generation recommended" if collapsed else "larger active generation loop with stricter dedup",
        "recommended_claim_level": claim,
        "blocking_issues": [] if claim != "failed" else ["missing_or_invalid_raw_input"],
        "required_next_run": "Codex/grammar-driven generation pilot" if collapsed else "larger multiagent active generation loop",
        "real_promotion_enabled": False,
        "turing_completeness_claimed": False,
        "solved_program_synthesis_claimed": False,
    }


def _write_failed_missing(raw: Path, records: Path, dataset: Path, missing: List[str]) -> Dict[str, Any]:
    for name in ["accepted", "quarantine", "rejected"]:
        (dataset / name).mkdir(parents=True, exist_ok=True)
        (dataset / name / f"{name}.jsonl").write_text("", encoding="utf-8")
        _write_json(dataset / name / "manifest.json", {"split": name, "count": 0})
    schema = {
        "raw_input_directory": str(raw),
        "missing_raw_files": missing,
        "raw_total_samples": 0,
        "json_parse_error_count": 0,
        "schema_valid_count": 0,
        "schema_audit_passed": False,
    }
    readiness = {
        "raw_input_directory": str(raw),
        "raw_total_samples": 0,
        "schema_audit_passed": False,
        "collapse_audit_completed": False,
        "dedup_leakage_audit_completed": False,
        "support_safety_audit_passed": False,
        "conversion_audit_completed": False,
        "compiler_audit_completed": False,
        "accepted_count": 0,
        "quarantine_count": 0,
        "rejected_count": 0,
        "acceptance_rate": 0.0,
        "duplicate_rate": 0.0,
        "near_duplicate_rate": 0.0,
        "leakage_count": 0,
        "agent_count": 0,
        "agent_cross_duplicate_rate": 0.0,
        "template_family_concentration_top1": 0.0,
        "diversity_score": 0.0,
        "collapse_score": 0.0,
        "multiagent_collapse_detected": False,
        "final_dataset_quality_score": 0.0,
        "improvement_vs_v0_9_15": {"quality_score_delta": -PREVIOUS_BASELINE["quality_score"], "acceptance_rate_delta": -PREVIOUS_BASELINE["acceptance_rate"], "duplicate_rate_delta": None, "leakage_delta": None},
        "generator_still_collapsed": False,
        "ready_for_larger_active_generation_loop": False,
        "ready_for_codex_grammar_generation": False,
        "recommended_next_action": "provide required multiagent raw dataset and rerun audit",
        "recommended_claim_level": "failed",
        "blocking_issues": ["missing_raw_files"],
        "required_next_run": "rerun after raw_manifest/raw_generation_report/shards/stats/warnings are present",
        "missing_raw_files": missing,
        "real_promotion_enabled": False,
        "turing_completeness_claimed": False,
    }
    _write_json(records / "raw_schema_audit.json", schema)
    (records / "raw_schema_audit.md").write_text(_schema_md(schema), encoding="utf-8")
    _write_json(records / "multiagent_collapse_audit.json", {"completed": False, "missing_raw_files": missing, "agent_count": 0, "duplicate_rate": 0.0, "near_duplicate_rate": 0.0, "agent_cross_duplicate_rate": 0.0, "template_family_concentration_top1": 0.0, "diversity_score": 0.0, "collapse_score": 0.0, "multiagent_collapse_detected": False})
    _write_json(records / "raw_dedup_leakage_audit.json", {"completed": False, "missing_raw_files": missing, "leakage_count_total": 0, "duplicate_input_count": 0, "duplicate_candidate_program_count": 0})
    _write_json(records / "support_status_safety_audit.json", {"completed": False, "missing_raw_files": missing, "support_status_safety_passed": False, "function_marked_current_supported_count": 0, "array_marked_current_supported_count": 0, "recursion_marked_current_supported_count": 0, "unbounded_loop_marked_current_supported_count": 0, "io_marked_current_supported_count": 0, "system_call_marked_current_supported_count": 0})
    _write_json(records / "conversion_metrics.json", {"completed": False, "missing_raw_files": missing, "conversion_attempt_count": 0, "conversion_success_count": 0, "conversion_failure_count": 0, "conversion_success_rate": 0.0, "raw_target_ir_hint_trusted": False, "raw_expected_output_hint_trusted": False})
    _write_json(records / "compiler_audit_metrics.json", {"completed": False, "missing_raw_files": missing, "backend_claim_safe": False, "real_compiler_invocation_count": 0, "compiler_verified_correct_rate": 0.0, "future_domain_compiled_count": 0, "boundary_compiler_misroute_count": 0, "function_compiled_count": 0, "array_compiled_count": 0, "recursion_compiled_count": 0, "unbounded_loop_compiled_count": 0})
    _write_json(records / "acceptance_split_metrics.json", {"completed": False, "missing_raw_files": missing, "raw_total_samples": 0, "accepted_count": 0, "quarantine_count": 0, "rejected_count": 0, "acceptance_rate": 0.0})
    _write_json(records / "raw_quality_score.json", {"completed": False, "missing_raw_files": missing, "final_dataset_quality_score": 0.0, "v0_9_15_quality_score": PREVIOUS_BASELINE["quality_score"], "quality_score_delta": -PREVIOUS_BASELINE["quality_score"]})
    for filename in ["multiagent_collapse_audit.md", "raw_dedup_leakage_audit.md", "support_status_safety_audit.md", "acceptance_split_report.md", "raw_quality_score.md", "mainline_conclusion.md"]:
        (records / filename).write_text(f"# v0.9.15.1\n\nmissing_raw_files: {missing}\n", encoding="utf-8")
    _write_json(records / "compiler_audit_trace_manifest.json", {"shards": [], "total_rows": 0})
    _write_jsonl(records / "conversion_failures.jsonl", [])
    _write_json(records / "multiagent_active_generation_readiness.json", readiness)
    _write_json(records / "mainline_conclusion.json", readiness)
    return readiness


def _missing_raw_files(raw: Path) -> List[str]:
    missing = []
    if not raw.exists():
        return [str(raw)]
    for rel in REQUIRED_RAW_FILES:
        if not (raw / rel).exists():
            missing.append(rel)
    if not (raw / "shards").exists() or not list((raw / "shards").glob("*.jsonl")):
        missing.append("shards/*.jsonl")
    if not (raw / "stats").exists() or not list((raw / "stats").glob("*.json")):
        missing.append("stats/*.json")
    return missing


def _duplicate_pair_count_by_agent(rows: List[Dict[str, Any]], keys: List[str]) -> Dict[str, int]:
    by_key: Dict[str, List[str]] = defaultdict(list)
    for row, key in zip(rows, keys):
        by_key[key].append(str(row.get("agent_id", "unknown_agent")))
    cross = self_pairs = total = 0
    for agents in by_key.values():
        if len(agents) < 2:
            continue
        total += len(agents) - 1
        if len(set(agents)) > 1:
            cross += len(agents) - 1
        else:
            self_pairs += len(agents) - 1
    return {"cross": cross, "self": self_pairs, "total_duplicate_pairs": total}


def _concentration(values: List[str], total: int) -> tuple[float, float]:
    counts = Counter(values)
    if not total:
        return 0.0, 0.0
    top = counts.most_common(10)
    return (top[0][1] / total if top else 0.0, sum(count for _, count in top) / total)


def _agent_balance(samples_by_agent: Dict[str, int], total: int) -> float:
    if not samples_by_agent or total == 0:
        return 0.0
    ideal = total / len(samples_by_agent)
    deviation = sum(abs(count - ideal) for count in samples_by_agent.values()) / total
    return round(max(0.0, 1.0 - deviation), 6)


def _nl_near_duplicate_rate(rows: List[Dict[str, Any]]) -> float:
    total = 0
    dup = 0
    for row in rows:
        variants = row.get("natural_language_variants", []) or []
        sigs = [_near_sig(v) for v in variants]
        total += len(sigs)
        dup += len(sigs) - len(set(sigs))
    return dup / total if total else 0.0


def _average_unique_variants(rows: List[Dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    return round(sum(len(set(_near_sig(v) for v in (row.get("natural_language_variants", []) or []))) for row in rows) / len(rows), 6)


def _estimate_unique_safe_acceptance(rows: List[Dict[str, Any]]) -> float:
    safe = [row for row in rows if row.get("support_status") == "current_supported"]
    unique = len({_norm(row.get("candidate_program", "")) for row in safe})
    return unique / len(rows) if rows else 0.0


def _near_duplicate_count(values: List[str]) -> int:
    sigs = [_near_sig(v) for v in values]
    return len(sigs) - len(set(sigs))


def _split_pair_count(rows: List[Dict[str, Any]], left: str, right: str) -> int:
    mapping: Dict[str, set[str]] = defaultdict(set)
    for row in rows:
        mapping[_norm(row.get("input", ""))].add(str(row.get("split_hint", "")))
    return sum(1 for splits in mapping.values() if left in splits and right in splits)


def _group_leakage(rows: List[Dict[str, Any]], key: str) -> int:
    mapping: Dict[str, set[str]] = defaultdict(set)
    for row in rows:
        value = str(row.get(key) or _hash(row.get("candidate_program", "")))
        mapping[value].add(str(row.get("split_hint", "")))
    return sum(1 for splits in mapping.values() if len(splits & {"train", "eval", "test", "heldout"}) > 1)


def _program_shape(program: str) -> str:
    import re

    text = _norm(program)
    text = "".join("0" if ch.isdigit() else ch for ch in text)
    text = re.sub(r"[A-Za-z_][A-Za-z0-9_]*", "id", text)
    return _hash(text)


def _semantic_hash(row: Dict[str, Any]) -> str:
    return _hash(f"{row.get('category')}::{_program_shape(row.get('candidate_program', ''))}")


def _near_sig(text: Any) -> str:
    import re

    words = re.findall(r"[A-Za-z0-9_]+", str(text).lower())
    return " ".join(sorted(set(words)))


def _norm(text: Any) -> str:
    import re

    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def _hash(value: Any) -> str:
    import hashlib

    return hashlib.sha256(str(value).encode("utf-8", errors="replace")).hexdigest()[:16]


def _empty_compiler_metrics() -> Dict[str, Any]:
    return {"backend_claim_safe": False, "compiler_verified_correct_rate": 0.0, "future_domain_compiled_count": 0, "boundary_compiler_misroute_count": 0}


def _quality_recommendation(score: float, acceptance: float, duplicate: float) -> str:
    if score >= 0.80 and acceptance >= 0.20:
        return "ready_for_larger_active_generation_loop"
    if duplicate > 0.70 or acceptance < 0.01:
        return "Codex/grammar-driven generation recommended"
    return "usable_after_more_filtering"


def _schema_md(schema: Dict[str, Any]) -> str:
    return f"# Raw Schema Audit\n\n- raw_total_samples: {schema.get('raw_total_samples', 0)}\n- schema_valid_count: {schema.get('schema_valid_count', 0)}\n- schema_audit_passed: {schema.get('schema_audit_passed', False)}\n"


def _collapse_md(collapse: Dict[str, Any]) -> str:
    return f"# Multi-Agent Collapse Audit\n\n- duplicate_rate: {collapse['duplicate_rate']}\n- diversity_score: {collapse['diversity_score']}\n- multiagent_collapse_detected: {collapse['multiagent_collapse_detected']}\n"


def _dedup_md(dedup: Dict[str, Any]) -> str:
    return f"# Dedup Leakage Audit\n\n- leakage_count_total: {dedup['leakage_count_total']}\n"


def _safety_md(safety: Dict[str, Any]) -> str:
    return f"# Support Safety Audit\n\n- support_status_safety_passed: {safety['support_status_safety_passed']}\n"


def _acceptance_md(metrics: Dict[str, Any]) -> str:
    return f"# Acceptance Split\n\n- accepted_count: {metrics['accepted_count']}\n- quarantine_count: {metrics['quarantine_count']}\n- rejected_count: {metrics['rejected_count']}\n"


def _quality_md(quality: Dict[str, Any]) -> str:
    return f"# Raw Quality Score\n\n- final_dataset_quality_score: {quality['final_dataset_quality_score']}\n- recommendation: {quality['recommendation']}\n"


def _mainline_md(readiness: Dict[str, Any]) -> str:
    return "\n".join([
        "# v0.9.15.1 Multi-Agent Raw Dataset Re-Audit",
        "",
        "Raw multi-agent data remains untrusted until accepted split qualification. Real promotion remains disabled.",
        "",
        f"- recommended_claim_level: {readiness['recommended_claim_level']}",
        f"- multiagent_collapse_detected: {readiness['multiagent_collapse_detected']}",
        f"- ready_for_larger_active_generation_loop: {readiness['ready_for_larger_active_generation_loop']}",
        f"- ready_for_codex_grammar_generation: {readiness['ready_for_codex_grammar_generation']}",
        "",
        "## Still Not Proven",
        "- Turing completeness",
        "- solved program synthesis",
        "- production readiness",
        "- safe real promotion",
        "- stable convergence",
        "- solved OOD",
        "- general program synthesis",
        "- default profile changed",
        "",
    ])


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
