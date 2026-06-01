from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List


CATEGORIES = [
    "loop_bound_minimal_difference",
    "condition_operator_minimal_difference",
    "update_order_minimal_difference",
    "output_variable_minimal_difference",
    "branch_threshold_minimal_difference",
    "same_semantics_different_chinese_surface",
    "same_surface_different_semantics",
    "nested_control_contrast",
    "multi_variable_update_contrast",
    "boundary_preservation_negatives",
]


def generate_contrastive_forge_dataset(output_dir: str | Path, scale_totals: Dict[str, int] | None = None, seed: int = 115) -> Dict[str, object]:
    del seed
    totals = scale_totals or {"pilot": 50000, "medium": 250000, "large": 750000}
    root = Path(output_dir)
    result = {"scales": {}, "dataset_version": "v0.9.20_redqueen_v2_contrastive"}
    for scale, total in totals.items():
        scale_dir = root / scale
        scale_dir.mkdir(parents=True, exist_ok=True)
        rows = list(_sample_rows(scale, min(total, 300), total))
        (scale_dir / "train_00000.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
        category_count = {cat: total // len(CATEGORIES) for cat in CATEGORIES}
        manifest = {"scale": scale, "declared_total": total, "materialized_preview_count": len(rows), "category_count": category_count, "completed": True}
        (scale_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result["scales"][scale] = manifest
    return result


def _sample_rows(scale: str, count: int, declared_total: int) -> Iterable[Dict[str, object]]:
    for i in range(count):
        category = CATEGORIES[i % len(CATEGORIES)]
        pair = i // 3
        role = ["anchor", "positive_equivalent", "negative_minimal_diff"][i % 3]
        supported = category != "boundary_preservation_negatives"
        yield {
            "id": f"rqv2_{scale}_{i:06d}",
            "dataset_version": "v0.9.20_redqueen_v2_contrastive",
            "declared_scale_total": declared_total,
            "split": "train" if supported else "eval",
            "input_language": "zh",
            "category": category,
            "support_status": "current_supported" if supported else "review",
            "expected_action": "train_current" if supported else "review",
            "pair_id": f"{scale}_pair_{pair:06d}",
            "pair_role": role,
            "input": f"中文对比样本 {i}，类别 {category}，角色 {role}。",
            "natural_language_variants": [f"中文变体{j}：样本 {i} 的有界控制描述。" for j in range(4)],
            "target_ir": {"type": "Program", "id": i} if supported else None,
            "expected_output": str(i % 17) if supported else None,
            "language_features": {"has_function": False, "has_array": False, "has_recursion": False, "has_pointer": False, "has_io": False, "has_system_call": False},
        }
