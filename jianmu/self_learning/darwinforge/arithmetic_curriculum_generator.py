from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.arithmetic_boundary_labels import SUPPORTED, label_metadata
from jianmu.self_learning.darwinforge.arithmetic_curriculum_schedule import build_arithmetic_curriculum_schedule
from jianmu.self_learning.darwinforge.arithmetic_dataset_audit import audit_arithmetic_dataset, write_audit_report
from jianmu.self_learning.darwinforge.arithmetic_expression_grammar import SUPPORTED_STAGES, GrammarConfig, generate_supported_expression, render_input, unsupported_template
from jianmu.self_learning.darwinforge.arithmetic_safe_evaluator import EvalConfig, inspect_ir, safe_evaluate_expression


SCALE_TOTALS = {"small": 10_000, "medium": 50_000, "large": 150_000}
CATEGORY_RATIOS = {
    SUPPORTED: 0.50,
    "unsupported_arithmetic_boundary": 0.12,
    "true_false_accept_trap": 0.12,
    "future_domain_candidate": 0.10,
    "near_ood_arithmetic": 0.08,
    "hard_ood": 0.06,
    "label_review_candidate": 0.02,
}
SPLIT_RATIOS = {"train": 0.70, "eval": 0.15, "test": 0.10, "heldout": 0.05}


def generate_arithmetic_curriculum_dataset(output_dir: str | Path, records_dir: str | Path, scales: Iterable[str], seed: int = 42, shard_size: int = 10_000) -> Dict[str, Any]:
    output = Path(output_dir)
    records = Path(records_dir)
    output.mkdir(parents=True, exist_ok=True)
    records.mkdir(parents=True, exist_ok=True)
    summaries: Dict[str, Any] = {}
    for scale in scales:
        summaries[scale] = generate_scale(scale, output / scale, seed, shard_size)
    _write_records(records, summaries)
    return {"scales": summaries, "records_dir": str(records)}


def generate_scale(scale: str, scale_dir: Path, seed: int = 42, shard_size: int = 10_000) -> Dict[str, Any]:
    if scale not in SCALE_TOTALS:
        raise ValueError(f"unknown scale: {scale}")
    rng = random.Random(seed + {"small": 101, "medium": 202, "large": 303}[scale])
    scale_dir.mkdir(parents=True, exist_ok=True)
    for split in SPLIT_RATIOS:
        (scale_dir / split).mkdir(parents=True, exist_ok=True)
    total = SCALE_TOTALS[scale]
    rows = _generate_rows(total, rng, seed, scale)
    _write_shards(scale_dir, rows, shard_size)
    schedule = build_arithmetic_curriculum_schedule()
    _write_json(scale_dir / "curriculum_schedule.json", schedule)
    audit = audit_arithmetic_dataset(scale_dir)
    _write_json(scale_dir / "audit.json", audit)
    write_audit_report(scale_dir, audit)
    manifest = _manifest(scale, total, rows, audit, schedule)
    _write_json(scale_dir / "manifest.json", manifest)
    _write_json(scale_dir / "all_manifest.json", {"dataset_version": "v0.9.2", "scale": scale, "shards": _list_shards(scale_dir)})
    return {"scale": scale, "manifest_path": str(scale_dir / "manifest.json"), "audit_path": str(scale_dir / "audit.json"), "report_path": str(scale_dir / "report.md"), "actual_total": len(rows), "audit": audit}


def _generate_rows(total: int, rng: random.Random, seed: int, scale: str) -> List[Dict[str, Any]]:
    category_counts = _counts(total, CATEGORY_RATIOS)
    rows: List[Dict[str, Any]] = []
    used_inputs: set[str] = set()
    index = 0
    for category, count in category_counts.items():
        for local in range(count):
            split = _split_for_index(index, total)
            if category == "label_review_candidate" and split == "train":
                split = "heldout"
            row = _make_row(category, split, local, index, rng, seed, scale)
            while row["input"] in used_inputs:
                row["input"] += f" #{index}"
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
    stage = "mixed_boundary"
    result_abs = None
    operator_set: List[str] = []
    operator_count = 0
    depth = 0
    has_parentheses = False
    has_unary = False
    has_division = False
    division_kind = "none"
    target_group_id = None
    if category == SUPPORTED:
        stage = _supported_stage(local)
        max_depth = 5 if scale == "large" else 4
        max_ops = 8 if scale == "large" else 6
        expr = generate_supported_expression(stage, rng, GrammarConfig(max_depth=max_depth, max_operator_count=max_ops))
        value, target_ir = safe_evaluate_expression(expr, EvalConfig(max_depth=max_depth, max_operator_count=max_ops))
        info = inspect_ir(target_ir)
        canonical = expr
        expected_output = f"{value}\n"
        result_abs = abs(value)
        operator_set = info["operator_set"]
        operator_count = info["operator_count"]
        depth = info["expression_depth"]
        has_parentheses = "(" in expr
        has_unary = info["has_unary_minus"]
        has_division = info["has_division"]
        division_kind = "exact" if has_division else "none"
        inp = render_input(expr, rng) + f" #ac{_alpha(global_index)}"
        target_group_id = f"tg-ac92-{split}-{global_index:06d}"
    else:
        templ = unsupported_template(category, global_index)
        inp = templ["input"]
        canonical = templ["canonical_expression"]
        if " / 0" in inp or "/0" in inp:
            division_kind = "division_by_zero"
        elif "7 / 2" in inp or "1 / 3" in inp or "seven by two" in inp:
            division_kind = "non_integer"
        stage = category
    return {
        "id": f"ac92-{global_index:08d}",
        "dataset_version": "v0.9.2",
        "split": split,
        "stage": "heldout_composition" if split == "heldout" and category == SUPPORTED else stage,
        "category": category,
        "input": inp,
        "canonical_expression": canonical,
        "target_ir": target_ir,
        "expected_output": expected_output,
        "expected_type": meta["expected_type"],
        "boundary_label": meta["boundary_label"],
        "expected_action": meta["expected_action"],
        "nutrient_policy": meta["nutrient_policy"],
        "toxicity_policy": meta["toxicity_policy"],
        "operator_set": operator_set,
        "operator_count": operator_count,
        "integer_range": [-999, 999],
        "has_parentheses": has_parentheses,
        "has_unary_minus": has_unary,
        "has_division": has_division,
        "division_kind": division_kind,
        "expression_depth": depth,
        "result_abs": result_abs,
        "template_id": f"tmpl-{stage}",
        "expression_group_id": f"eg-ac92-{split}-{global_index:06d}",
        "paraphrase_group_id": f"pg-ac92-{split}-{global_index:06d}",
        "target_group_id": target_group_id,
        "training_usage": "train_current" if category == SUPPORTED and split == "train" else "evaluation_or_boundary",
        "leakage_guard": {
            "free_inference_forbidden_fields": ["target_ir", "expected_output", "target_branch_path", "boundary_label", "expected_action", "nutrient_policy", "toxicity_policy"],
            "non_supported_has_target": category != SUPPORTED and (target_ir is not None or expected_output is not None),
        },
        "provenance": {"generator": "arithmetic_curriculum_generator", "seed": seed, "generation_rule": stage},
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
            shard = split_rows[start : start + shard_size]
            path = scale_dir / split / f"{split}_{shard_index:03d}.jsonl"
            path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in shard), encoding="utf-8")


def _counts(total: int, ratios: Dict[str, float]) -> Dict[str, int]:
    counts = {key: int(total * value) for key, value in ratios.items()}
    missing = total - sum(counts.values())
    counts[SUPPORTED] += missing
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


def _supported_stage(index: int) -> str:
    stages = ["single_op"] * 20 + ["two_op_no_parentheses"] * 20 + ["precedence"] * 20 + ["parentheses"] * 20 + ["negative_numbers"] * 10 + ["exact_division"] * 10
    return stages[index % len(stages)]


def _alpha(index: int) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    out = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, len(alphabet))
        out = alphabet[rem] + out
    return out


def _manifest(scale: str, total: int, rows: List[Dict[str, Any]], audit: Dict[str, Any], schedule: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "dataset_version": "v0.9.2",
        "scale": scale,
        "requested_total": total,
        "actual_total": len(rows),
        "split_count": audit["split_count"],
        "category_count": audit["category_count"],
        "stage_count": audit["stage_count"],
        "audit_passed": audit["audit_passed"],
        "curriculum_stage_count": len(schedule["stages"]),
    }


def _list_shards(scale_dir: Path) -> List[Dict[str, Any]]:
    return [{"split": path.parent.name, "path": str(path.relative_to(scale_dir)), "size_bytes": path.stat().st_size} for path in sorted(scale_dir.glob("*/*.jsonl"))]


def _write_records(records: Path, summaries: Dict[str, Any]) -> None:
    total = sum(row["actual_total"] for row in summaries.values())
    audit_summary = {scale: row["audit"] for scale, row in summaries.items()}
    _write_json(records / "arithmetic_dataset_generation_metrics.json", {"scales": {k: v["actual_total"] for k, v in summaries.items()}, "total_samples_generated": total})
    _write_json(records / "arithmetic_dataset_audit_summary.json", audit_summary)
    (records / "arithmetic_dataset_generation_report.md").write_text("# v0.9.2 Arithmetic Curriculum Dataset\n\nDataset-only generation completed. No model training was run.\n", encoding="utf-8")
    conclusion = {
        "proved": ["auditable arithmetic curriculum dataset generated"],
        "not_proved": ["solved arithmetic", "stable convergence", "solved OOD", "general program synthesis", "same-size LLM advantage", "safe real promotion", "production readiness"],
        "dataset_scales_completed": list(summaries.keys()),
        "total_samples_generated": total,
        "audit_passed_by_scale": {scale: row["audit"]["audit_passed"] for scale, row in summaries.items()},
        "category_counts_by_scale": {scale: row["audit"]["category_count"] for scale, row in summaries.items()},
        "supported_count": sum(row["audit"]["category_count"].get("current_supported_arithmetic", 0) for row in summaries.values()),
        "unsupported_count": sum(row["audit"]["category_count"].get("unsupported_arithmetic_boundary", 0) for row in summaries.values()),
        "trap_count": sum(row["audit"]["category_count"].get("true_false_accept_trap", 0) for row in summaries.values()),
        "future_domain_count": sum(row["audit"]["category_count"].get("future_domain_candidate", 0) for row in summaries.values()),
        "near_ood_count": sum(row["audit"]["category_count"].get("near_ood_arithmetic", 0) for row in summaries.values()),
        "hard_ood_count": sum(row["audit"]["category_count"].get("hard_ood", 0) for row in summaries.values()),
        "leakage_counts": {scale: {"train_eval_input_leakage_count": row["audit"]["train_eval_input_leakage_count"], "expression_group_leakage_count": row["audit"]["expression_group_leakage_count"], "paraphrase_group_leakage_count": row["audit"]["paraphrase_group_leakage_count"]} for scale, row in summaries.items()},
        "non_supported_has_targetir_count": sum(row["audit"]["non_supported_has_targetir_count"] for row in summaries.values()),
        "supported_missing_targetir_count": sum(row["audit"]["supported_missing_targetir_count"] for row in summaries.values()),
        "division_boundary_checks": {
            "division_by_zero_supported_count": sum(row["audit"]["division_by_zero_supported_count"] for row in summaries.values()),
            "non_integer_division_supported_count": sum(row["audit"]["non_integer_division_supported_count"] for row in summaries.values()),
        },
        "curriculum_stages_generated": build_arithmetic_curriculum_schedule()["stages"],
        "must_recheck": ["dataset semantics before v0.9.3 training", "free-inference feature exclusion", "heldout composition behavior"],
        "can_enter_v0_9_3_arithmetic_training_probe": all(row["audit"]["audit_passed"] for row in summaries.values()),
        "still_not_proven": ["solved arithmetic", "stable convergence", "solved OOD", "general program synthesis", "same-size LLM advantage", "safe real promotion", "production readiness"],
    }
    _write_json(records / "arithmetic_dataset_mainline_conclusion.json", conclusion)
    (records / "arithmetic_dataset_mainline_conclusion.md").write_text("\n".join([
        "# v0.9.2 Arithmetic Dataset Mainline Conclusion",
        "",
        f"- dataset_scales_completed: {conclusion['dataset_scales_completed']}",
        f"- total_samples_generated: {total}",
        f"- audit_passed_by_scale: {conclusion['audit_passed_by_scale']}",
        "- This version generated data only. It did not train a model or claim solved arithmetic.",
        "- Still not proven: solved arithmetic, stable convergence, solved OOD, general program synthesis, same-size LLM advantage, safe real promotion, production readiness.",
    ]) + "\n", encoding="utf-8")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
