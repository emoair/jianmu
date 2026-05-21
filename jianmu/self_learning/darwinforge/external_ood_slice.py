from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List


EXTERNAL_OOD_COUNTS = {"quick": 800, "medium": 3000, "large": 8000}


CATEGORY_TO_BOUNDARY = {
    "external_hard_ood": ("hard_ood", "hard_ood"),
    "external_arithmetic_traps": ("true_false_accept_trap", "true_false_accept_trap"),
    "external_future_domain": ("future_domain_candidate", "future_domain_candidate"),
    "external_near_ood": ("near_ood_generalization_candidate", "near_ood_generalization_candidate"),
}


TEMPLATES = {
    "external_hard_ood": [
        "写一段关于春天的短文",
        "画一张城市夜景图",
        "请和我闲聊一下周末计划",
        "描述蓝色给人的感觉",
        "写一个 HTTP server 的需求说明",
        "这不是编程任务，只要安慰一句",
    ],
    "external_arithmetic_traps": [
        "写一首关于 {a}+{b} 的诗",
        "不要计算 {a}+{b}",
        "输出字符串“三加四”而不是结果",
        "解释 {a} 和 {b} 的区别",
        "分别说明 {a} 和 {b}，不要求求和",
        "把 {a}+{b} 作为标题",
    ],
    "external_future_domain": [
        "What is {a} plus {b}?",
        "计算 {a}.5 + {b}.25",
        "求 x + {a} = {b} 中 x 的值",
        "计算 {a} / {b}，允许非整除",
        "计算 {a} 的平方根",
        "写一个循环求数组和",
    ],
    "external_near_ood": [
        "帮我算一下三加四",
        "麻烦给出 {a}+{b} 的结果",
        "请计算 {a}+{b}",
        "求十二除以三",
        "算算看 {a} 乘 {b}",
        "给我一个 {a}-{b} 的答案",
    ],
}


def generate_external_ood_slice(mode: str = "quick", output_dir: str | Path | None = None) -> Dict:
    total = EXTERNAL_OOD_COUNTS[mode]
    categories = list(TEMPLATES)
    rows: List[Dict] = []
    idx = 0
    while len(rows) < total:
        category = categories[idx % len(categories)]
        template = TEMPLATES[category][idx % len(TEMPLATES[category])]
        a = 3 + (idx % 17)
        b = 2 + (idx % 11)
        raw = template.format(a=a, b=b)
        input_mode, boundary_label = CATEGORY_TO_BOUNDARY[category]
        rows.append(
            {
                "sample_id": f"external_ood_{mode}_{idx:06d}",
                "raw_text": raw,
                "canonical_text": raw,
                "input_mode": input_mode,
                "external_ood_category": category,
                "expected_boundary_action": _expected_action(boundary_label),
                "evaluation_only_label": boundary_label,
                "boundary_label": boundary_label,
                "source_version": "v0.8.8_external_ood",
                "source_reason": category,
            }
        )
        idx += 1

    manifest = {
        "mode": mode,
        "external_ood_total_count": len(rows),
        "category_distribution": dict(Counter(row["external_ood_category"] for row in rows)),
        "contains_training_rows": False,
        "contains_target_ir": False,
        "contains_expected_output": False,
    }

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        _write_jsonl(output_dir / "external_ood_slice.jsonl", rows)
        (output_dir / "external_ood_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (output_dir / "external_ood_report.md").write_text(_report(manifest), encoding="utf-8")

    return {"samples": rows, "manifest": manifest}


def _expected_action(boundary_label: str) -> str:
    if boundary_label in {"hard_ood", "true_false_accept_trap"}:
        return "reject"
    if boundary_label == "future_domain_candidate":
        return "future_buffer"
    if boundary_label == "near_ood_generalization_candidate":
        return "quarantine"
    return "unknown"


def _write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _report(manifest: Dict) -> str:
    return "\n".join(
        [
            "# External OOD Slice（外部分布外切片）",
            "",
            f"- mode: {manifest['mode']}",
            f"- external_ood_total_count: {manifest['external_ood_total_count']}",
            f"- category_distribution: {manifest['category_distribution']}",
            "- This slice is evaluation-only（仅用于评估） and is not training data.",
        ]
    ) + "\n"
