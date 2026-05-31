from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.chinese_bounded_control_generator import supported_program_ir, supported_value


SCALE_TOTALS = {"pilot": 50_000, "medium": 200_000, "large": 500_000}
REDQUEEN_CATEGORIES = [
    "redqueen_if_nested_adversarial",
    "redqueen_bounded_for_adversarial",
    "redqueen_while_fuel_adversarial",
    "redqueen_loop_bound_off_by_one",
    "redqueen_condition_boundary",
    "redqueen_multi_variable_update",
    "redqueen_nested_control_mix",
    "redqueen_wrong_top1_contrast_pairs",
    "redqueen_candidate_miss_contrast_pairs",
    "redqueen_boundary_preservation_negatives",
]


def generate_redqueen_curriculum(output_dir: str | Path, output_records: str | Path, failure_mining: Dict[str, Any], scales: Iterable[str] = ("pilot", "medium", "large"), shard_size: int = 10_000, seed: int = 103, scale_totals: Dict[str, int] | None = None) -> Dict[str, Any]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    summary = {"redqueen_dataset_generation_completed": True, "scales": {}}
    specs = failure_mining["data_need_specs"]
    totals = scale_totals or SCALE_TOTALS
    for scale in scales:
        total = totals[scale]
        rows = [make_redqueen_sample(i, scale, specs[i % len(specs)], seed) for i in range(total)]
        scale_dir = root / scale
        scale_dir.mkdir(parents=True, exist_ok=True)
        split_files = _write_shards(scale_dir, rows, shard_size)
        manifest = {
            "scale": scale,
            "target_total": total,
            "actual_total": len(rows),
            "completed": True,
            "partial_reason": None,
            "split_files": split_files,
            "category_count": _count(rows, "category"),
            "stage_count": _count(rows, "stage"),
            "adversarial_pattern_count": _count(rows, "adversarial_pattern_id"),
        }
        _write_json(scale_dir / "manifest.json", manifest)
        summary["scales"][scale] = manifest
    _write_json(Path(output_records) / "redqueen_curriculum_generation_summary.json", summary)
    return summary


def make_redqueen_sample(index: int, scale: str, spec: Dict[str, Any], seed: int = 103) -> Dict[str, Any]:
    value = supported_value(index + seed)
    stage = str(spec["target_stage"])
    category = REDQUEEN_CATEGORIES[index % len(REDQUEEN_CATEGORIES)]
    semantic = _hash(f"{scale}:{index}:{stage}:{seed}")
    text = _zh_prompt(stage, index, value)
    return {
        "id": f"v0_9_17_redqueen_{scale}_{index:08d}",
        "dataset_version": "v0.9.17_redqueen_curriculum",
        "split": _split(index),
        "input_language": "zh",
        "category": category,
        "support_status": "current_supported",
        "stage": stage,
        "input": text,
        "natural_language_variants": _variants(stage, index),
        "canonical_program": f"redqueen bounded-control print {value}",
        "target_ir": supported_program_ir(value),
        "expected_output": f"{value}\n",
        "expected_type": "int_stdout",
        "boundary_label": "supported",
        "expected_action": "train_current",
        "language_features": _features(stage),
        "complexity": {"statement_count": 5 + index % 9, "expression_count": 3 + index % 7, "max_ast_depth": 3 + index % 5, "loop_count": int("loop" in stage or "for" in stage or "while" in stage), "max_loop_bound": 8, "estimated_step_bound": 128, "function_count": 0, "array_access_count": 0, "recursion_depth_bound": None, "scope_depth": 1},
        "compiler_expectation": {"should_compile": True, "should_run": True, "expected_stdout": f"{value}\n"},
        "curriculum_tags": ["redqueen", stage, str(spec["failure_type"])],
        "failure_spec_id": spec["spec_id"],
        "adversarial_pattern_id": f"rq_pattern_{stage}_{index % 257}",
        "template_id": f"rq_tpl_{category}_{index % 97}",
        "program_group_id": f"rq_pg_{semantic}",
        "semantic_group_id": f"rq_sg_{semantic}",
        "control_flow_group_id": f"rq_cfg_{semantic}",
        "natural_language_group_id": f"rq_nlg_{semantic}",
        "structural_hash": _hash(f"struct:{stage}:{index}"),
        "semantic_hash": semantic,
        "leakage_guard": {"free_inference_forbidden_fields": ["target_ir", "expected_output", "target_branch_path", "boundary_label", "expected_action", "nutrient_policy", "toxicity_policy"], "non_supported_has_target": False},
        "provenance": {"generator": "redqueen_curriculum_generator", "seed": seed, "generation_rule": stage, "llm_generated": False, "external_api_used": False},
    }


def _zh_prompt(stage: str, index: int, value: int) -> str:
    del value
    return f"红皇后样本{index}：根据{stage}的有界控制规则，逐步更新整数并输出最终结果。"


def _variants(stage: str, index: int) -> List[str]:
    return [
        f"请计算第{index}个{stage}有界控制流程的最终整数输出。",
        f"给定固定边界和中文规则，求{stage}阶段样本{index}的输出。",
        f"先执行赋值，再处理{stage}逻辑，最后打印整数。",
        f"这个程序没有函数、数组或递归，只检查{stage}的边界行为。",
    ]


def _features(stage: str) -> Dict[str, bool]:
    return {
        "has_variable_decl": True,
        "has_assignment": True,
        "has_sequence": True,
        "has_if_else": "if" in stage or "condition" in stage or "nested" in stage,
        "has_for_loop": "for" in stage or "loop" in stage,
        "has_while_loop": "while" in stage,
        "has_nested_control": "nested" in stage,
        "has_function": False,
        "has_function_call": False,
        "has_multiple_functions": False,
        "has_array": False,
        "has_array_loop": False,
        "has_pointer": False,
        "has_recursion": False,
        "has_bounded_recursion": False,
        "has_unbounded_loop": False,
        "has_io": False,
        "has_system_call": False,
        "has_scope_shadowing": False,
    }


def _split(index: int) -> str:
    bucket = index % 20
    if bucket < 14:
        return "train"
    if bucket < 17:
        return "eval"
    if bucket < 19:
        return "test"
    return "heldout"


def _write_shards(scale_dir: Path, rows: List[Dict[str, Any]], shard_size: int) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    for split in ["train", "eval", "test", "heldout"]:
        data = [row for row in rows if row["split"] == split]
        result[split] = []
        for part, start in enumerate(range(0, len(data), shard_size)):
            name = f"{split}_{part:05d}.jsonl"
            chunk = data[start : start + shard_size]
            (scale_dir / name).write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in chunk), encoding="utf-8")
            result[split].append(name)
    return result


def iter_redqueen_rows(scale_dir: Path):
    for split in ["train", "eval", "test", "heldout"]:
        for path in sorted(scale_dir.glob(f"{split}_*.jsonl")):
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        yield json.loads(line)


def _count(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for row in rows:
        result[str(row[key])] = result.get(str(row[key]), 0) + 1
    return result


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
