from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.turing_frontier_v2_grammar import CATEGORY_PLAN, is_current_supported, stage_for_category, support_status_for_category


DEFAULT_SCALE_TOTALS = {"pilot": 50_000, "medium": 250_000, "large": 1_000_000}


def generate_turing_frontier_v2_dataset(output_dir: str | Path, records_dir: str | Path, scales: Iterable[str] = ("pilot", "medium", "large"), seed: int = 96, shard_size: int = 10_000) -> Dict[str, Any]:
    del seed
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    summary = {"dataset_v2_generation_completed": True, "scales": {}}
    for scale in scales:
        total = DEFAULT_SCALE_TOTALS[scale]
        scale_dir = root / scale
        scale_dir.mkdir(parents=True, exist_ok=True)
        counts = _category_counts(total)
        rows = _rows_for_counts(scale, counts)
        split_rows = _split_rows(rows)
        for split, items in split_rows.items():
            split_dir = scale_dir / split
            split_dir.mkdir(parents=True, exist_ok=True)
            for shard_index in range(0, len(items), shard_size):
                shard = items[shard_index: shard_index + shard_size]
                (split_dir / f"shard_{shard_index // shard_size:05d}.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in shard), encoding="utf-8")
        manifest = {"dataset_version": "v0.9.14_turing_frontier_v2", "scale": scale, "actual_total": len(rows), "target_total": total, "completed": True, "category_count": counts, "splits": {k: len(v) for k, v in split_rows.items()}}
        _write_json(scale_dir / "manifest.json", manifest)
        _write_json(scale_dir / "curriculum_schedule.json", {"scale": scale, "stages": sorted({row["stage"] for row in rows}), "current_supported_categories": [cat for cat in CATEGORY_PLAN if is_current_supported(cat)]})
        summary["scales"][scale] = manifest
    Path(records_dir).mkdir(parents=True, exist_ok=True)
    _write_json(Path(records_dir) / "dataset_v2_generation_summary.json", summary)
    return summary


def make_frontier_v2_sample(index: int, scale: str, category: str) -> Dict[str, Any]:
    supported = is_current_supported(category)
    status = support_status_for_category(category)
    split = _split_for_index(index, status)
    expected = str((index % 17) + 1) if supported else None
    target_ir = _supported_print_ir(int(expected)) if supported else None
    features = _features(category)
    return {
        "id": f"v0_9_14_{scale}_{index:08d}",
        "dataset_version": "v0.9.14_turing_frontier_v2",
        "split": split,
        "stage": stage_for_category(category),
        "category": category,
        "support_status": status,
        "input": _input_text(category, index),
        "natural_language_variants": [_input_text(category, index), f"variant {_letters(index % 26)} for {category}"],
        "canonical_program": f"print {expected}" if supported else None,
        "target_ir": target_ir,
        "expected_output": expected + "\n" if supported else None,
        "expected_type": "int_stdout" if supported else status,
        "boundary_label": "supported" if supported else status,
        "expected_action": "train_current" if supported and split == "train" else ("accept_supported" if supported else ("human_review" if status == "review" else "isolate_future" if status == "future_domain" else "reject")),
        "language_features": features,
        "complexity": _complexity(category, index),
        "compiler_expectation": {"should_compile": supported, "should_run": supported, "expected_stdout": expected + "\n" if supported else None},
        "curriculum_tags": [stage_for_category(category), status],
        "template_id": f"tpl_{category}_{index % 31}",
        "program_group_id": f"pg_{category}_{index // 10}",
        "control_flow_group_id": f"cfg_{stage_for_category(category)}_{index // 20}",
        "frontier_group_id": f"fg_{category}_{index // 50}",
        "natural_language_group_id": f"nlg_{category}_{index}",
        "leakage_guard": {"free_inference_forbidden_fields": ["target_ir", "expected_output", "target_branch_path", "boundary_label", "expected_action", "nutrient_policy", "toxicity_policy"], "non_supported_has_target": not supported and (target_ir is not None or expected is not None)},
        "provenance": {"generator": "turing_frontier_v2_generator", "seed": 96, "generation_rule": category, "llm_generated": False},
    }


def _category_counts(total: int) -> Dict[str, int]:
    counts = {cat: int(total * spec["ratio"]) for cat, spec in CATEGORY_PLAN.items()}
    delta = total - sum(counts.values())
    counts["current_supported_bounded_substrate"] += delta
    return counts


def _supported_print_ir(value: int) -> Dict[str, Any]:
    return {"op": "Program", "body": [{"op": "Print", "value": {"op": "Int", "value": value}}]}


def _rows_for_counts(scale: str, counts: Dict[str, int]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    index = 0
    for category, count in counts.items():
        for _ in range(count):
            rows.append(make_frontier_v2_sample(index, scale, category))
            index += 1
    return rows


def _split_rows(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    result = {"train": [], "eval": [], "test": [], "heldout": []}
    for row in rows:
        result[row["split"]].append(row)
    return result


def _split_for_index(index: int, status: str) -> str:
    if status == "review":
        return ["eval", "test", "heldout"][index % 3]
    bucket = index % 20
    if bucket < 14:
        return "train"
    if bucket < 17:
        return "eval"
    if bucket < 19:
        return "test"
    return "heldout"


def _features(category: str) -> Dict[str, bool]:
    return {
        "has_variable_decl": True,
        "has_assignment": category in {"current_supported_bounded_substrate", "bounded_control_hard_supported", "scope_lifetime_edge_cases"},
        "has_sequence": True,
        "has_if_else": "if" in category or category in {"current_supported_bounded_substrate", "bounded_control_hard_supported"},
        "has_for_loop": "loop" in category or category in {"current_supported_bounded_substrate", "bounded_control_hard_supported"},
        "has_while_loop": "unbounded_loop" in category or category == "current_supported_bounded_substrate",
        "has_nested_control": category == "bounded_control_hard_supported",
        "has_function": "function" in category or "recursion" in category,
        "has_function_call": "function" in category or "recursion" in category,
        "has_multiple_functions": category == "future_function_call_graph",
        "has_array": "array" in category,
        "has_array_loop": "array_loop" in category,
        "has_pointer": False,
        "has_recursion": "recursion" in category,
        "has_bounded_recursion": category == "future_bounded_recursion_candidate",
        "has_unbounded_loop": category == "unsupported_unbounded_loop",
        "has_io": category == "trap_unsafe_io_system",
        "has_system_call": category == "trap_unsafe_io_system",
        "has_scope_shadowing": category == "scope_lifetime_edge_cases",
    }


def _complexity(category: str, index: int) -> Dict[str, Any]:
    f = _features(category)
    return {"statement_count": 3 + index % 7, "expression_count": 2 + index % 5, "max_ast_depth": 2 + index % 6, "loop_count": int(f["has_for_loop"] or f["has_while_loop"]), "max_loop_bound": 8 if f["has_for_loop"] and not f["has_unbounded_loop"] else None, "estimated_step_bound": 64 if support_status_for_category(category) == "current_supported" else None, "function_count": 2 if f["has_multiple_functions"] else int(f["has_function"]), "array_access_count": 2 if f["has_array"] else 0, "recursion_depth_bound": 4 if f["has_bounded_recursion"] else None, "scope_depth": 2 if f["has_scope_shadowing"] else 1}


def _input_text(category: str, index: int) -> str:
    return f"vtwo {category} sample {_letters(index)} compute the bounded result"


def _letters(index: int) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    if index == 0:
        return alphabet[0]
    chars = []
    value = index
    while value:
        chars.append(alphabet[value % len(alphabet)])
        value //= len(alphabet)
    return "".join(reversed(chars))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
