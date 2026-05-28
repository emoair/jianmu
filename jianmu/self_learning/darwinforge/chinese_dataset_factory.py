from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.chinese_bounded_control_generator import canonical_program, supported_program_ir, supported_value
from jianmu.self_learning.darwinforge.chinese_program_description_grammar import boundary_input, detect_input_language, zh_variants


SCALE_TOTALS = {"pilot": 50_000, "medium": 250_000, "large": 1_000_000}
CATEGORY_RATIOS = {
    "current_supported_bounded_substrate_zh": 0.30,
    "bounded_control_hard_supported_zh": 0.25,
    "near_supported_pure_function_zh": 0.08,
    "near_supported_fixed_array_zh": 0.08,
    "future_bounded_recursion_candidate_zh": 0.05,
    "unsupported_unbounded_loop_zh": 0.05,
    "unsupported_unbounded_recursion_zh": 0.04,
    "scope_lifetime_edge_cases_zh": 0.03,
    "trap_unsafe_io_system_zh": 0.03,
    "adversarial_instruction_trap_zh": 0.02,
    "hard_ood_chinese_unrelated": 0.02,
    "english_unrelated_request": 0.02,
    "mixed_language_boundary": 0.02,
    "label_review_candidate": 0.01,
}
SUPPORTED = {"current_supported_bounded_substrate_zh", "bounded_control_hard_supported_zh"}


def generate_codex_grammar_chinese_dataset(output_dir: str | Path, records_dir: str | Path, scales: Iterable[str], seed: int = 98, shard_size: int = 10000) -> Dict[str, Any]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    summary = {"dataset_generation_completed": True, "scales": {}}
    for scale in scales:
        rows = _generate_scale(scale, SCALE_TOTALS[scale], seed)
        scale_dir = root / scale
        scale_dir.mkdir(parents=True, exist_ok=True)
        split_files = _write_split_shards(scale_dir, rows, shard_size)
        manifest = {"scale": scale, "target_total": SCALE_TOTALS[scale], "actual_total": len(rows), "completed": True, "partial_reason": None, "category_count": _count(rows, "category"), "input_language_count": _count(rows, "input_language"), "shard_size": shard_size, "split_files": split_files}
        _write_json(scale_dir / "manifest.json", manifest)
        summary["scales"][scale] = manifest
    Path(records_dir).mkdir(parents=True, exist_ok=True)
    _write_json(Path(records_dir) / "chinese_dataset_generation_summary.json", summary)
    return summary


def _write_split_shards(scale_dir: Path, rows: List[Dict[str, Any]], shard_size: int) -> Dict[str, List[str]]:
    split_files: Dict[str, List[str]] = {}
    for split in ["train", "eval", "test", "heldout"]:
        data = [row for row in rows if row["split"] == split]
        split_files[split] = []
        for part, start in enumerate(range(0, len(data), shard_size)):
            chunk = data[start : start + shard_size]
            name = f"{split}_{part:05d}.jsonl"
            (scale_dir / name).write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in chunk), encoding="utf-8")
            split_files[split].append(name)
    return split_files


def make_sample(index: int, scale: str, category: str, seed: int = 98) -> Dict[str, Any]:
    is_supported = category in SUPPORTED
    split = _split_for_index(index, category)
    if is_supported:
        value = supported_value(index)
        text = zh_variants(category, index)[0]
        variants = zh_variants(category, index)
        input_language = "zh"
        status = "current_supported"
        target_ir = supported_program_ir(value)
        expected = f"{value}\n"
        action = "train_current"
        canonical = canonical_program(value, hard=category.startswith("bounded_control_hard"))
    else:
        text, variants, input_language = boundary_input(category, index)
        status = _status(category)
        target_ir = None
        expected = None
        action = _action(status)
        canonical = None
    semantic = _hash(f"{category}:{index}:{seed}")
    return {
        "id": f"v0_9_15_2_{scale}_{index:08d}",
        "dataset_version": "v0.9.15.2_codex_grammar_chinese",
        "split": split,
        "input_language": input_language,
        "category": category,
        "support_status": status,
        "stage": "codex_grammar_chinese_factory",
        "input": text,
        "natural_language_variants": variants,
        "canonical_program": canonical,
        "target_ir": target_ir,
        "expected_output": expected,
        "expected_type": (
            "int_stdout"
            if is_supported
            else "future"
            if status in {"near_supported", "future_domain"}
            else "trap"
            if status == "trap"
            else "review"
            if status == "review"
            else "unsupported"
        ),
        "boundary_label": "supported" if is_supported else status,
        "expected_action": action,
        "language_features": _features(category),
        "complexity": _complexity(category, index),
        "compiler_expectation": {"should_compile": is_supported, "should_run": is_supported, "expected_stdout": expected},
        "curriculum_tags": [category, status, input_language],
        "template_id": f"tpl_{category}_{index % 97}",
        "template_family_id": f"tf_{category}_{index % 997}",
        "program_group_id": f"pg_{semantic}",
        "semantic_group_id": f"sg_{semantic}",
        "control_flow_group_id": f"cfg_{semantic}",
        "natural_language_group_id": f"nlg_{semantic}",
        "language_domain_group_id": f"ld_{input_language}_{index}",
        "structural_hash": _hash(f"struct:{category}:{index}"),
        "semantic_hash": semantic,
        "leakage_guard": {"free_inference_forbidden_fields": ["target_ir", "expected_output", "target_branch_path", "boundary_label", "expected_action", "nutrient_policy", "toxicity_policy"], "non_supported_has_target": (not is_supported) and (target_ir is not None or expected is not None)},
        "provenance": {"generator": "codex_grammar_chinese_generator", "seed": seed, "generation_rule": category, "llm_generated": False, "external_api_used": False},
    }


def _generate_scale(scale: str, total: int, seed: int) -> List[Dict[str, Any]]:
    counts = {cat: int(total * ratio) for cat, ratio in CATEGORY_RATIOS.items()}
    counts["current_supported_bounded_substrate_zh"] += total - sum(counts.values())
    rows: List[Dict[str, Any]] = []
    index = 0
    for category, count in counts.items():
        for _ in range(count):
            rows.append(make_sample(index, scale, category, seed))
            index += 1
    return rows


def _status(category: str) -> str:
    if category.startswith("near_supported"):
        return "near_supported"
    if category.startswith("future"):
        return "future_domain"
    if category.startswith("unsupported"):
        return "unsupported"
    if category.startswith("trap") or category.startswith("adversarial"):
        return "trap"
    if category.startswith("hard_ood") or category.startswith("english"):
        return "hard_ood"
    return "review"


def _action(status: str) -> str:
    return {"near_supported": "isolate_future", "future_domain": "isolate_future", "unsupported": "reject", "trap": "reject", "hard_ood": "reject", "review": "review"}[status]


def _split_for_index(index: int, category: str) -> str:
    if category == "label_review_candidate":
        return ["eval", "test", "heldout"][index % 3]
    b = index % 20
    if b < 14:
        return "train"
    if b < 17:
        return "eval"
    if b < 19:
        return "test"
    return "heldout"


def _features(category: str) -> Dict[str, bool]:
    return {
        "has_variable_decl": category not in {"hard_ood_chinese_unrelated", "english_unrelated_request"},
        "has_assignment": category in SUPPORTED or "scope" in category,
        "has_sequence": True,
        "has_if_else": category in SUPPORTED,
        "has_for_loop": category in SUPPORTED or "loop" in category,
        "has_while_loop": "while" in category or "unbounded_loop" in category,
        "has_nested_control": category == "bounded_control_hard_supported_zh",
        "has_function": "function" in category or "recursion" in category,
        "has_function_call": "function" in category or "recursion" in category,
        "has_multiple_functions": False,
        "has_array": "array" in category,
        "has_array_loop": "array" in category,
        "has_pointer": False,
        "has_recursion": "recursion" in category,
        "has_bounded_recursion": "bounded_recursion" in category,
        "has_unbounded_loop": "unbounded_loop" in category,
        "has_io": "io" in category,
        "has_system_call": "system" in category or "io" in category,
        "has_scope_shadowing": "scope" in category,
    }


def _complexity(category: str, index: int) -> Dict[str, Any]:
    f = _features(category)
    return {"statement_count": 3 + index % 9, "expression_count": 2 + index % 7, "max_ast_depth": 2 + index % 5, "loop_count": int(f["has_for_loop"] or f["has_while_loop"]), "max_loop_bound": 10 if f["has_for_loop"] and not f["has_unbounded_loop"] else None, "estimated_step_bound": 128 if category in SUPPORTED else None, "function_count": int(f["has_function"]), "array_access_count": 2 if f["has_array"] else 0, "recursion_depth_bound": 6 if f["has_bounded_recursion"] else None, "scope_depth": 2 if f["has_scope_shadowing"] else 1}


def _count(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for row in rows:
        result[row[key]] = result.get(row[key], 0) + 1
    return result


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
