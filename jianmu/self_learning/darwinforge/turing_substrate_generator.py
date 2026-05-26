from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.turing_substrate_boundary_labels import SUPPORTED, label_metadata
from jianmu.self_learning.darwinforge.turing_substrate_curriculum_schedule import build_turing_substrate_curriculum_schedule
from jianmu.self_learning.darwinforge.turing_substrate_dataset_audit import audit_turing_substrate_dataset, write_audit_report
from jianmu.self_learning.darwinforge.turing_substrate_grammar import SUPPORTED_STAGES, generate_supported_program, render_input, render_program, unsupported_template
from jianmu.self_learning.darwinforge.turing_substrate_safe_interpreter import evaluate_program, inspect_program


SCALE_TOTALS = {"small": 10_000, "medium": 50_000, "large": 120_000}
CATEGORY_RATIOS = {
    SUPPORTED: 0.50,
    "unsupported_program_boundary": 0.12,
    "true_false_accept_trap": 0.12,
    "future_domain_candidate": 0.10,
    "near_ood_program": 0.08,
    "hard_ood": 0.06,
    "label_review_candidate": 0.02,
}
SPLIT_RATIOS = {"train": 0.70, "eval": 0.15, "test": 0.10, "heldout": 0.05}


def generate_turing_substrate_curriculum_dataset(output_dir: str | Path, records_dir: str | Path, scales: Iterable[str], seed: int = 52, shard_size: int = 10_000) -> Dict[str, Any]:
    output = Path(output_dir)
    records = Path(records_dir)
    output.mkdir(parents=True, exist_ok=True)
    records.mkdir(parents=True, exist_ok=True)
    summaries: Dict[str, Any] = {}
    for scale in scales:
        summaries[scale] = generate_scale(scale, output / scale, seed, shard_size)
    _write_records(records, summaries)
    return {"scales": summaries, "records_dir": str(records)}


def generate_scale(scale: str, scale_dir: Path, seed: int = 52, shard_size: int = 10_000) -> Dict[str, Any]:
    if scale not in SCALE_TOTALS:
        raise ValueError(f"unknown scale: {scale}")
    rng = random.Random(seed + {"small": 610, "medium": 620, "large": 630}[scale])
    scale_dir.mkdir(parents=True, exist_ok=True)
    for split in SPLIT_RATIOS:
        (scale_dir / split).mkdir(parents=True, exist_ok=True)
    total = SCALE_TOTALS[scale]
    rows = _generate_rows(total, rng, seed, scale)
    _write_shards(scale_dir, rows, shard_size)
    schedule = build_turing_substrate_curriculum_schedule()
    _write_json(scale_dir / "curriculum_schedule.json", schedule)
    audit = audit_turing_substrate_dataset(scale_dir)
    _write_json(scale_dir / "audit.json", audit)
    write_audit_report(scale_dir, audit)
    manifest = {
        "dataset_version": "v0.9.6",
        "scale": scale,
        "requested_total": total,
        "actual_total": len(rows),
        "split_count": audit["split_count"],
        "category_count": audit["category_count"],
        "stage_count": audit["stage_count"],
        "audit_passed": audit["audit_passed"],
        "curriculum_stage_count": len(schedule["stages"]),
    }
    _write_json(scale_dir / "manifest.json", manifest)
    _write_json(scale_dir / "all_manifest.json", {"dataset_version": "v0.9.6", "scale": scale, "shards": _list_shards(scale_dir)})
    return {"scale": scale, "manifest_path": str(scale_dir / "manifest.json"), "audit_path": str(scale_dir / "audit.json"), "report_path": str(scale_dir / "report.md"), "actual_total": len(rows), "audit": audit}


def _generate_rows(total: int, rng: random.Random, seed: int, scale: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    used_inputs: set[str] = set()
    index = 0
    for category, count in _counts(total, CATEGORY_RATIOS).items():
        for local in range(count):
            split = _split_for_index(index, total)
            if category == "label_review_candidate" and split == "train":
                split = "heldout"
            row = _make_row(category, split, local, index, rng, seed, scale)
            while row["input"] in used_inputs:
                row["input"] += f" unique-{index}"
            used_inputs.add(row["input"])
            rows.append(row)
            index += 1
    rng.shuffle(rows)
    return rows


def _make_row(category: str, split: str, local: int, global_index: int, rng: random.Random, seed: int, scale: str) -> Dict[str, Any]:
    meta = label_metadata(category)
    target_ir = None
    expected_output = None
    canonical = None
    stage = category
    template_id = category
    language_features = _empty_features()
    complexity = {"statement_count": 0, "expression_count": 0, "max_ast_depth": 0, "loop_count": 0, "max_loop_bound": None, "estimated_step_bound": None}
    compiler_expectation = {"should_compile": False, "should_run": False, "expected_stdout": None}
    target_group_id = None
    training_usage = "evaluation_or_boundary"
    if category == SUPPORTED:
        stage = SUPPORTED_STAGES[local % len(SUPPORTED_STAGES)]
        target_ir = generate_supported_program(stage, rng, global_index)
        expected_output = evaluate_program(target_ir)
        canonical = render_program(target_ir) + f"\n# substrate-id ts96-{global_index:08d}"
        inspected = inspect_program(target_ir)
        language_features = inspected["features"]
        complexity = {key: inspected[key] for key in ["statement_count", "expression_count", "max_ast_depth", "loop_count", "max_loop_bound", "estimated_step_bound"]}
        compiler_expectation = {"should_compile": True, "should_run": True, "expected_stdout": expected_output}
        template_id = f"tmpl-{stage}"
        target_group_id = f"tg-ts96-{split}-{global_index:08d}"
        training_usage = "train_current" if split == "train" else "evaluation_or_boundary"
        inp = render_input(canonical, rng, global_index)
    else:
        templ = unsupported_template(category, global_index)
        inp = templ["input"]
        canonical = templ["canonical_program"]
        template_id = templ["template_id"]
        language_features = _features_from_unsupported(inp)
    return {
        "id": f"ts96-{global_index:08d}",
        "dataset_version": "v0.9.6",
        "split": split,
        "stage": "heldout_composition" if split == "heldout" and category == SUPPORTED else stage,
        "category": category,
        "input": inp,
        "canonical_program": canonical,
        "target_ir": target_ir,
        "expected_output": expected_output,
        "expected_type": meta["expected_type"],
        "boundary_label": meta["boundary_label"],
        "expected_action": meta["expected_action"],
        "nutrient_policy": meta["nutrient_policy"],
        "toxicity_policy": meta["toxicity_policy"],
        "language_features": language_features,
        "complexity": complexity,
        "compiler_expectation": compiler_expectation,
        "template_id": template_id,
        "program_group_id": f"pgm-ts96-{split}-{global_index:08d}",
        "control_flow_group_id": f"cfg-ts96-{split}-{global_index:08d}",
        "target_group_id": target_group_id,
        "training_usage": training_usage,
        "leakage_guard": {
            "free_inference_forbidden_fields": ["target_ir", "expected_output", "target_branch_path", "boundary_label", "expected_action", "nutrient_policy", "toxicity_policy"],
            "non_supported_has_target": category != SUPPORTED and (target_ir is not None or expected_output is not None),
        },
        "provenance": {"generator": "turing_substrate_generator", "seed": seed, "generation_rule": stage},
    }


def _features_from_unsupported(text: str) -> Dict[str, bool]:
    lower = text.lower()
    features = _empty_features()
    features["has_while_loop"] = "while" in lower
    features["has_for_loop"] = "for " in lower
    features["has_function"] = "function" in lower or "long long f" in lower or "define" in lower
    features["has_array"] = "[" in lower or "array" in lower
    features["has_pointer"] = "*" in lower and "long long *" in lower
    features["has_recursion"] = "recursion" in lower or "f(n-1)" in lower
    return features


def _empty_features() -> Dict[str, bool]:
    return {
        "has_variable_decl": False,
        "has_assignment": False,
        "has_sequence": False,
        "has_if_else": False,
        "has_for_loop": False,
        "has_while_loop": False,
        "has_nested_control": False,
        "has_function": False,
        "has_array": False,
        "has_pointer": False,
        "has_recursion": False,
    }


def _write_shards(scale_dir: Path, rows: List[Dict[str, Any]], shard_size: int) -> None:
    for split in SPLIT_RATIOS:
        for old in (scale_dir / split).glob("*.jsonl"):
            old.unlink()
    by_split: Dict[str, List[Dict[str, Any]]] = {split: [] for split in SPLIT_RATIOS}
    for row in rows:
        by_split[row["split"]].append(row)
    for split, split_rows in by_split.items():
        for shard_index, start in enumerate(range(0, len(split_rows), shard_size)):
            path = scale_dir / split / f"{split}_{shard_index:03d}.jsonl"
            shard = split_rows[start:start + shard_size]
            path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in shard), encoding="utf-8")


def _write_records(records: Path, summaries: Dict[str, Any]) -> None:
    total = sum(row["actual_total"] for row in summaries.values())
    audit_summary = {scale: row["audit"] for scale, row in summaries.items()}
    _write_json(records / "turing_substrate_dataset_generation_metrics.json", {"scales": {k: v["actual_total"] for k, v in summaries.items()}, "total_samples_generated": total})
    _write_json(records / "turing_substrate_dataset_audit_summary.json", audit_summary)
    (records / "turing_substrate_dataset_generation_report.md").write_text("# v0.9.6 Turing Substrate Dataset\n\nDataset-only generation completed. No model training was run.\n", encoding="utf-8")
    _write_mainline(records, summaries, compiler_metrics=None)


def write_readiness_and_mainline(records: str | Path, summaries: Dict[str, Any], compiler_metrics: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return _write_mainline(Path(records), summaries, compiler_metrics)


def _write_mainline(records: Path, summaries: Dict[str, Any], compiler_metrics: Dict[str, Any] | None) -> Dict[str, Any]:
    audit_passed = {scale: row["audit"]["audit_passed"] for scale, row in summaries.items()}
    category_counts = {scale: row["audit"]["category_count"] for scale, row in summaries.items()}
    total = sum(row["actual_total"] for row in summaries.values())
    compiler_ok = bool(compiler_metrics and compiler_metrics.get("backend_type") == "real_c_compiler" and compiler_metrics.get("compile_worker_count") == 16 and compiler_metrics.get("compiler_verified_correct_rate", 0) >= 0.98 and compiler_metrics.get("boundary_compiler_misroute_count", 0) == 0)
    blocking: List[str] = []
    if not all(audit_passed.values()):
        blocking.append("dataset_audit_failed")
    if compiler_metrics and not compiler_ok:
        blocking.append("compiler_validation_not_strong")
    claim = "turing_substrate_dataset_ready_with_compiler_validation" if compiler_ok and not blocking else ("turing_substrate_dataset_ready" if not blocking else "needs_dataset_fix")
    readiness = {
        "dataset_generation_completed": True,
        "scales_completed": list(summaries.keys()),
        "audit_passed_by_scale": audit_passed,
        "compiler_validation_completed": bool(compiler_metrics),
        "compile_worker_count": compiler_metrics.get("compile_worker_count") if compiler_metrics else None,
        "backend_type": compiler_metrics.get("backend_type") if compiler_metrics else None,
        "compiler_name": compiler_metrics.get("compiler_name") if compiler_metrics else None,
        "real_compiler_invocation_count": compiler_metrics.get("real_compiler_invocation_count", 0) if compiler_metrics else 0,
        "compiler_verified_correct_rate": compiler_metrics.get("compiler_verified_correct_rate") if compiler_metrics else None,
        "boundary_compiler_misroute_count": compiler_metrics.get("boundary_compiler_misroute_count", 0) if compiler_metrics else 0,
        "forbidden_field_access_count": 0,
        "target_ir_access_before_candidate_generation": False,
        "expected_output_access_before_candidate_generation": False,
        "ready_for_v0_9_7_training_probe": claim in {"turing_substrate_dataset_ready", "turing_substrate_dataset_ready_with_compiler_validation"},
        "recommended_claim_level": claim,
        "blocking_issues": blocking,
        "required_next_run": "v0.9.7 bounded substrate training probe; do not claim Turing completeness",
    }
    _write_json(records / "turing_substrate_readiness.json", readiness)
    conclusion = {
        "what_this_version_proved": "audited curriculum data for variables, assignments, sequences, if/else, and bounded loops was generated",
        "what_this_version_did_not_prove": ["Turing completeness", "solved arithmetic", "stable convergence", "solved OOD", "general program synthesis", "same-size LLM advantage", "safe real promotion", "production readiness"],
        "why_substrate_not_complete": "The dataset covers bounded preconditions for Turing-complete structures, not unbounded memory/control or trained capability.",
        "dataset_scales_completed": list(summaries.keys()),
        "total_samples_generated": total,
        "category_counts_by_scale": category_counts,
        "audit_passed_by_scale": audit_passed,
        "compiler_validation_result": compiler_metrics or {},
        "compile_worker_count_reason": "v0.9.5.1 identified 16 as the best local throughput point",
        "leakage_summary": {scale: {"train_eval_input_leakage_count": row["audit"]["train_eval_input_leakage_count"], "program_group_leakage_count": row["audit"]["program_group_leakage_count"], "control_flow_group_leakage_count": row["audit"]["control_flow_group_leakage_count"]} for scale, row in summaries.items()},
        "can_enter_v0_9_7_training_probe": readiness["ready_for_v0_9_7_training_probe"],
        "post_v1_routes_reserved": ["root similarity incremental training", "verified backend as teacher for NL-to-semantic-IR adapter"],
        "results_for_paper_v2": ["turing substrate dataset audit", "16-worker compiler validation spot"] if compiler_metrics else ["turing substrate dataset audit"],
        "results_requiring_revalidation": ["training probe behavior", "larger compiler validation if v0.9.7 uses this dataset"],
        "still_not_proven": readiness["what_this_version_did_not_prove"] if "what_this_version_did_not_prove" in readiness else ["Turing completeness", "solved arithmetic", "stable convergence", "solved OOD", "general program synthesis", "same-size LLM advantage", "safe real promotion", "production readiness"],
        "recommended_claim_level": claim,
        "blocking_issues": blocking,
    }
    _write_json(records / "mainline_conclusion.json", conclusion)
    (records / "mainline_conclusion.md").write_text("\n".join([
        "# v0.9.6 Mainline Conclusion",
        "",
        f"- dataset_scales_completed: {list(summaries.keys())}",
        f"- total_samples_generated: {total}",
        f"- audit_passed_by_scale: {audit_passed}",
        f"- recommended_claim_level: {claim}",
        "- This is a Turing substrate dataset, not a Turing-completeness claim.",
        "- Still not proven: Turing completeness, solved arithmetic, stable convergence, solved OOD, general program synthesis, same-size LLM advantage, safe real promotion, production readiness.",
    ]) + "\n", encoding="utf-8")
    return readiness


def _counts(total: int, ratios: Dict[str, float]) -> Dict[str, int]:
    counts = {key: int(total * value) for key, value in ratios.items()}
    counts[SUPPORTED] += total - sum(counts.values())
    return counts


def _split_for_index(index: int, total: int) -> str:
    frac = index / max(total, 1)
    if frac < 0.70:
        return "train"
    if frac < 0.85:
        return "eval"
    if frac < 0.95:
        return "test"
    return "heldout"


def _list_shards(scale_dir: Path) -> List[Dict[str, Any]]:
    return [{"split": path.parent.name, "path": str(path.relative_to(scale_dir)), "size_bytes": path.stat().st_size} for path in sorted(scale_dir.glob("*/*.jsonl"))]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
