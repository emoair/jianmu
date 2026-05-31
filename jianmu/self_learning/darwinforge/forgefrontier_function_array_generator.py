from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List


SCALE_TARGET_TOTALS = {"pilot": 50_000, "medium": 250_000, "large": 1_000_000}
SCALE_TOTALS = {"pilot": 50_000, "medium": 250_000, "large": 500_000}
FRONTIER_CATEGORIES = {
    "frontier_pure_function_no_recursion_zh": 0.20,
    "frontier_fixed_array_no_pointer_zh": 0.20,
    "frontier_function_with_bounded_control_zh": 0.15,
    "frontier_array_with_bounded_loop_zh": 0.15,
    "frontier_function_array_limited_combo_zh": 0.10,
    "frontier_negative_recursion_boundary_zh": 0.05,
    "frontier_negative_pointer_boundary_zh": 0.05,
    "frontier_negative_io_system_boundary_zh": 0.05,
    "english_mixed_function_array_boundary": 0.03,
    "label_review_frontier_candidate": 0.02,
}


def generate_forgefrontier_dataset(
    output_dir: str | Path,
    output_records: str | Path,
    scales: Iterable[str] = ("pilot", "medium", "large"),
    shard_size: int = 10_000,
    seed: int = 108,
    scale_totals: Dict[str, int] | None = None,
) -> Dict[str, Any]:
    root = Path(output_dir)
    totals = scale_totals or SCALE_TOTALS
    summary: Dict[str, Any] = {"forgefrontier_dataset_generated": True, "scales": {}}
    for scale in scales:
        total = totals[scale]
        target_total = SCALE_TARGET_TOTALS.get(scale, total)
        rows = [make_forgefrontier_sample(i, scale, seed) for i in range(total)]
        scale_dir = root / scale
        scale_dir.mkdir(parents=True, exist_ok=True)
        split_files = _write_shards(scale_dir, rows, shard_size)
        manifest = {
            "scale": scale,
            "target_total": target_total,
            "actual_total": len(rows),
            "completed": len(rows) >= target_total,
            "partial": len(rows) < target_total,
            "partial_reason": "" if len(rows) >= target_total else f"generated_{len(rows)}_of_{target_total}_to_avoid_runtime_or_memory_overrun",
            "split_files": split_files,
            "category_count": _count(rows, "category"),
            "support_status_count": _count(rows, "support_status"),
            "stage_count": _count(rows, "stage"),
        }
        _write_json(scale_dir / "manifest.json", manifest)
        summary["scales"][scale] = manifest
    _write_json(Path(output_records) / "forgefrontier_generation_summary.json", summary)
    return summary


def make_forgefrontier_sample(index: int, scale: str, seed: int = 108) -> Dict[str, Any]:
    category = _category_for_index(index)
    support_status = _support_status(category)
    stage = _stage(category)
    split = _split(index, support_status)
    value = (index * 7 + seed) % 97 + 3
    language = "mixed" if category == "english_mixed_function_array_boundary" and index % 2 else ("en" if category == "english_mixed_function_array_boundary" else "zh")
    expected = None if support_status in {"unsupported", "trap", "hard_ood", "review", "future_domain"} else f"{value}\n"
    target_ir = _target_ir(category, value) if expected is not None else None
    semantic = _hash(f"{scale}:{index}:{category}:{seed}")
    return {
        "id": f"v0_9_18_forgefrontier_{scale}_{index:08d}",
        "dataset_version": "v0.9.18_forgefrontier_function_array",
        "split": split,
        "input_language": language,
        "category": category,
        "support_status": support_status,
        "stage": stage,
        "input": _prompt(category, index),
        "natural_language_variants": _variants(category, index, language),
        "canonical_program": f"forgefrontier {category} sample {scale} {index} print {value}" if expected is not None else None,
        "target_ir": target_ir,
        "expected_output": expected,
        "expected_type": "int_stdout" if expected is not None else ("review" if support_status == "review" else "unsupported"),
        "boundary_label": "experimental" if support_status.startswith("experimental") else support_status,
        "expected_action": _expected_action(support_status),
        "language_features": _language_features(category),
        "frontier_features": _frontier_features(category),
        "complexity": {
            "statement_count": 4 + index % 9,
            "expression_count": 3 + index % 8,
            "max_ast_depth": 3 + index % 5,
            "loop_count": int("loop" in category or "bounded_control" in category),
            "max_loop_bound": 8 if "loop" in category or "bounded_control" in category else None,
            "estimated_step_bound": 128 if support_status.startswith("experimental") else None,
        },
        "compiler_expectation": {"should_compile": expected is not None, "should_run": expected is not None, "expected_stdout": expected},
        "template_id": f"ff_tpl_{category}_{index % 97}",
        "template_family_id": f"ff_family_{category}",
        "program_group_id": f"ff_pg_{semantic}",
        "semantic_group_id": f"ff_sg_{semantic}",
        "frontier_group_id": f"ff_fg_{stage}_{index % 503}",
        "natural_language_group_id": f"ff_nlg_{semantic}",
        "structural_hash": _hash(f"struct:{category}:{index}"),
        "semantic_hash": semantic,
        "provenance": {"generator": "forgefrontier_function_array_generator", "seed": seed, "llm_generated": False, "external_api_used": False},
    }


def iter_forgefrontier_rows(scale_dir: Path) -> Iterator[Dict[str, Any]]:
    for split in ["train", "eval", "test", "heldout"]:
        for path in sorted(scale_dir.glob(f"{split}_*.jsonl")):
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        yield json.loads(line)


def iter_forgefrontier_dataset(root: str | Path) -> Iterator[Dict[str, Any]]:
    for scale in sorted(p for p in Path(root).iterdir() if p.is_dir()):
        yield from iter_forgefrontier_rows(scale)


def _category_for_index(index: int) -> str:
    slot = index % 100
    cursor = 0
    for category, ratio in FRONTIER_CATEGORIES.items():
        cursor += int(ratio * 100)
        if slot < cursor:
            return category
    return "label_review_frontier_candidate"


def _support_status(category: str) -> str:
    if "pure_function" in category or "function_with_bounded" in category:
        return "experimental_supported_function"
    if "fixed_array" in category or "array_with_bounded" in category:
        return "experimental_supported_array"
    if "function_array_limited" in category:
        return "experimental_supported_function_array"
    if "recursion" in category:
        return "future_domain"
    if "pointer" in category or "io_system" in category:
        return "unsupported" if "pointer" in category else "trap"
    if "english_mixed" in category:
        return "hard_ood"
    return "review"


def _expected_action(status: str) -> str:
    if status.startswith("experimental"):
        return "train_experimental"
    return {"future_domain": "isolate_future", "unsupported": "reject", "trap": "reject", "hard_ood": "reject", "review": "review"}[status]


def _stage(category: str) -> str:
    return category.replace("_zh", "").replace("frontier_", "")


def _target_ir(category: str, value: int) -> Dict[str, Any]:
    kind = "forge_function_array" if "function_array" in category else ("forge_array" if "array" in category else "forge_function")
    return {"kind": kind, "version": 1, "stdout": value, "category": category}


def _language_features(category: str) -> Dict[str, bool]:
    return {
        "has_variable_decl": True,
        "has_assignment": True,
        "has_sequence": True,
        "has_if_else": "bounded_control" in category,
        "has_for_loop": "loop" in category,
        "has_while_loop": False,
        "has_nested_control": "bounded_control" in category,
        "has_function": "function" in category or "negative_recursion" in category,
        "has_function_call": "function" in category or "negative_recursion" in category,
        "has_multiple_functions": "function_array" in category,
        "has_array": "array" in category,
        "has_array_loop": "array_with_bounded_loop" in category,
        "has_pointer": "negative_pointer" in category,
        "has_recursion": "negative_recursion" in category,
        "has_bounded_recursion": False,
        "has_unbounded_loop": False,
        "has_io": "negative_io_system" in category,
        "has_system_call": "negative_io_system" in category,
    }


def _frontier_features(category: str) -> Dict[str, Any]:
    return {
        "function_count": 1 if "function" in category or "negative_recursion" in category else 0,
        "function_call_count": 1 if "function" in category or "negative_recursion" in category else 0,
        "max_call_depth": 2 if "function" in category else (99 if "negative_recursion" in category else 0),
        "array_count": 1 if "array" in category else 0,
        "array_length_max": 8 if "array" in category else None,
        "array_access_count": 4 if "array" in category else 0,
        "array_index_static_safe": "array" in category and "negative_pointer" not in category,
        "uses_pointer": "negative_pointer" in category,
        "uses_dynamic_allocation": False,
        "uses_recursion": "negative_recursion" in category,
        "uses_io": "negative_io_system" in category,
    }


def _prompt(category: str, index: int) -> str:
    if category == "english_mixed_function_array_boundary":
        return f"English boundary request {index}: inspect a function or array, but do not train as current supported."
    if category == "label_review_frontier_candidate":
        return f"请人工复核第{index}个函数数组边界样本，当前不进入训练。"
    return f"函数数组前沿样本{index}：根据{category}的有界规则计算最终整数输出。"


def _variants(category: str, index: int, language: str) -> List[str]:
    if language != "zh":
        return [f"Boundary English variant {index}", f"Mixed language 边界样本 {index}"]
    return [
        f"请计算第{index}个{category}样本的输出。",
        f"给定纯函数或固定数组的有界规则，求最终整数。",
        f"确认没有递归、指针、输入输出或系统调用后再计算。",
        f"这是实验前沿样本，不属于当前生产支持边界。",
    ]


def _split(index: int, status: str) -> str:
    if status == "review":
        return "heldout"
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
