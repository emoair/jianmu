from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.turing_frontier_boundary_labels import boundary_label_for_category, expected_action_for_category, is_supported_category
from jianmu.self_learning.darwinforge.turing_frontier_curriculum_schedule import write_frontier_schedule
from jianmu.self_learning.darwinforge.turing_frontier_grammar import complexity_for, expected_output_for_supported, language_features_for, simple_supported_ir


SCALE_TOTALS = {"small": 20_000, "medium": 80_000, "large": 200_000}
CATEGORY_RATIOS = [
    ("current_supported_bounded_substrate", 0.35),
    ("bounded_control_hard_supported", 0.15),
    ("future_function_candidate", 0.10),
    ("future_array_candidate", 0.10),
    ("future_recursion_candidate", 0.08),
    ("unsupported_unbounded_loop", 0.07),
    ("near_ood_program", 0.05),
    ("true_false_accept_trap", 0.05),
    ("hard_ood", 0.03),
    ("label_review_candidate", 0.02),
]
SPLITS = [("train", 0.70), ("eval", 0.15), ("test", 0.10), ("heldout", 0.05)]
SUPPORTED_STAGES = ["variable_declaration", "assignment_sequence", "multi_variable_sequence", "if_else_basic", "if_else_nested", "bounded_for_loop", "bounded_while_with_fuel", "nested_bounded_control"]


def generate_turing_frontier_dataset(output_dir: str | Path, records_dir: str | Path, scales: Iterable[str], seed: int = 68, shard_size: int = 10_000) -> Dict[str, Any]:
    output = Path(output_dir)
    records = Path(records_dir)
    output.mkdir(parents=True, exist_ok=True)
    records.mkdir(parents=True, exist_ok=True)
    summaries: Dict[str, Any] = {}
    for scale in scales:
        total = SCALE_TOTALS[scale]
        rows = [_make_row(scale, index, total, seed) for index in range(total)]
        _write_scale(output / scale, rows, shard_size)
        manifest = _manifest(scale, rows, seed, shard_size)
        (output / scale / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_frontier_schedule(output / scale / "curriculum_schedule.json")
        summaries[scale] = manifest
    metrics = {"dataset_generation_completed": True, "scales_completed": list(summaries), "by_scale": summaries}
    (records / "turing_frontier_dataset_generation_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (records / "turing_frontier_dataset_generation_report.md").write_text("# Turing Frontier Dataset Generation\n\nGenerated v0.9.9 frontier curriculum data. This is not a Turing-completeness claim.\n", encoding="utf-8")
    return metrics


def _make_row(scale: str, index: int, total: int, seed: int) -> Dict[str, Any]:
    category = _category_for_index(index, total)
    split = _split_for_index(index, total)
    rng = random.Random(seed * 1_000_003 + index)
    value = rng.randint(1, 17)
    stage = _stage_for(category, rng)
    supported = is_supported_category(category)
    target_ir = simple_supported_ir(value, stage if stage in SUPPORTED_STAGES else "bounded_for_loop") if supported else None
    expected_output = expected_output_for_supported(value, stage if stage in SUPPORTED_STAGES else "bounded_for_loop") if supported else None
    input_text = _input_for(category, stage, value, index)
    row_id = f"v0.9.9-{scale}-{index:07d}-{_hash(input_text)}"
    training_usage = "train_current" if split == "train" and supported else ("review" if category == "label_review_candidate" else "eval_or_boundary")
    return {
        "id": row_id,
        "dataset_version": "v0.9.9",
        "split": split,
        "stage": stage,
        "category": category,
        "input": input_text,
        "canonical_program": f"{stage}:{value}" if supported else None,
        "target_ir": target_ir,
        "expected_output": expected_output,
        "expected_type": "int_stdout" if supported else ("future" if category.startswith("future_") else ("review" if category == "label_review_candidate" else "unsupported")),
        "boundary_label": boundary_label_for_category(category),
        "expected_action": expected_action_for_category(category),
        "training_usage": training_usage,
        "nutrient_policy": {"supported_correct": 1.0 if supported else 0.0},
        "toxicity_policy": {"false_accept_toxic": 1.0 if not supported else 0.0},
        "language_features": language_features_for(category, stage),
        "complexity": complexity_for(category, stage, value),
        "compiler_expectation": {"should_compile": supported, "should_run": supported, "expected_stdout": expected_output},
        "template_id": f"tpl_{stage}_{rng.randint(0, 30)}",
        "program_group_id": f"pg_{scale}_{index}",
        "control_flow_group_id": f"cfg_{stage}_{index}",
        "target_group_id": f"tg_{stage}_{value}" if supported else None,
        "frontier_group_id": f"fg_{category}_{index}",
        "leakage_guard": {"free_inference_forbidden_fields": ["target_ir", "expected_output", "target_branch_path", "boundary_label", "expected_action", "nutrient_policy", "toxicity_policy"], "non_supported_has_target": bool((not supported) and (target_ir or expected_output))},
        "provenance": {"generator": "turing_frontier_generator", "seed": seed, "generation_rule": category},
    }


def _category_for_index(index: int, total: int) -> str:
    cursor = 0
    for category, ratio in CATEGORY_RATIOS:
        cursor += int(total * ratio)
        if index < cursor:
            return category
    return CATEGORY_RATIOS[-1][0]


def _split_for_index(index: int, total: int) -> str:
    pos = index
    cursor = 0
    for split, ratio in SPLITS:
        cursor += int(total * ratio)
        if pos < cursor:
            return split
    return "heldout"


def _stage_for(category: str, rng: random.Random) -> str:
    if category == "current_supported_bounded_substrate":
        return rng.choice(SUPPORTED_STAGES)
    if category == "bounded_control_hard_supported":
        return "bounded_control_hard_supported"
    return {
        "future_function_candidate": "future_function",
        "future_array_candidate": "future_array",
        "future_recursion_candidate": "future_recursion",
        "unsupported_unbounded_loop": "unsupported_unbounded_loop",
        "near_ood_program": "near_ood_program",
        "true_false_accept_trap": "true_false_accept_trap",
        "hard_ood": "hard_ood",
        "label_review_candidate": "label_review_candidate",
    }[category]


def _input_for(category: str, stage: str, value: int, index: int) -> str:
    if is_supported_category(category):
        return f"bounded program {index}: use {stage} and print the final integer"
    return {
        "future_function_candidate": f"future function program {index}: define f(x) and call it",
        "future_array_candidate": f"future array program {index}: fill a fixed array and read a[i]",
        "future_recursion_candidate": f"future recursion program {index}: recursive factorial style call",
        "unsupported_unbounded_loop": f"unsupported program {index}: while condition without fuel may not terminate",
        "near_ood_program": f"near ood program {index}: very large loop bound and ambiguous scope",
        "true_false_accept_trap": f"trap program {index}: asks for system call or user input",
        "hard_ood": f"hard ood text {index}: unrelated symbolic junk",
        "label_review_candidate": f"review candidate {index}: ambiguous frontier structure",
    }[category]


def _write_scale(scale_dir: Path, rows: List[Dict[str, Any]], shard_size: int) -> None:
    for split, _ratio in SPLITS:
        split_dir = scale_dir / split
        split_dir.mkdir(parents=True, exist_ok=True)
        split_rows = [row for row in rows if row["split"] == split]
        for shard_index in range(0, len(split_rows), shard_size):
            shard = split_rows[shard_index: shard_index + shard_size]
            name = f"data_{shard_index // shard_size:04d}.jsonl"
            (split_dir / name).write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in shard), encoding="utf-8")


def _manifest(scale: str, rows: List[Dict[str, Any]], seed: int, shard_size: int) -> Dict[str, Any]:
    return {
        "dataset_version": "v0.9.9",
        "scale": scale,
        "actual_total": len(rows),
        "seed": seed,
        "shard_size": shard_size,
        "category_count": dict(Counter(row["category"] for row in rows)),
        "split_count": dict(Counter(row["split"] for row in rows)),
        "stage_count": dict(Counter(row["stage"] for row in rows)),
    }


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
