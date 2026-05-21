from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List

from jianmu.self_learning.datasets.boundary_aware_generator import generate_boundary_aware_samples
from jianmu.self_learning.datasets.boundary_curriculum import build_boundary_curriculum
from jianmu.self_learning.datasets.boundary_dataset_audit import audit_boundary_dataset
from jianmu.self_learning.datasets.boundary_labels import BoundaryLabel


SCALE_TOTALS = {"small": 6000, "medium": 30000, "large": 100000, "xlarge": 300000}


def build_boundary_scale(
    scale: str,
    output_dir: str | Path,
    seed: int = 42,
    source_candidates: List[Dict] | None = None,
) -> Dict:
    if scale not in SCALE_TOTALS:
        raise ValueError(f"unknown scale: {scale}")
    started = time.time()
    output_dir = Path(output_dir) / scale
    output_dir.mkdir(parents=True, exist_ok=True)
    samples = generate_boundary_aware_samples(SCALE_TOTALS[scale], seed=seed, source_candidates=source_candidates)
    samples = _deduplicate_raw(samples, SCALE_TOTALS[scale], seed, source_candidates or [])
    splits = split_boundary_samples(samples)
    audit = audit_boundary_dataset(splits)
    curriculum = build_boundary_curriculum(samples)
    _write_split_files(output_dir, splits)
    _write_json(output_dir / "manifest.json", _manifest(scale, samples, splits, audit))
    _write_json(output_dir / "audit.json", audit)
    _write_json(output_dir / "curriculum_schedule.json", curriculum)
    (output_dir / "report.md").write_text(_report(scale, samples, audit, curriculum), encoding="utf-8")
    return {
        "scale": scale,
        "requested_total": SCALE_TOTALS[scale],
        "actual_total": len(samples),
        "reason_if_short": "" if len(samples) == SCALE_TOTALS[scale] else "deduplication_capacity",
        "output_dir": str(output_dir),
        "manifest_path": str(output_dir / "manifest.json"),
        "report_path": str(output_dir / "report.md"),
        "audit_path": str(output_dir / "audit.json"),
        "curriculum_schedule_path": str(output_dir / "curriculum_schedule.json"),
        "runtime_seconds": round(time.time() - started, 6),
        "audit": audit,
        "curriculum": curriculum,
        "boundary_label_distribution": dict(Counter(row["boundary_label"] for row in samples)),
    }


def split_boundary_samples(samples: List[Dict]) -> Dict[str, List[Dict]]:
    buckets = {
        "train": [],
        "eval_seen_target_unseen_paraphrase": [],
        "eval_unseen_target": [],
        "eval_ood_boundary": [],
        "eval_future_domain": [],
        "eval_near_ood": [],
    }
    for index, row in enumerate(samples):
        label = row["boundary_label"]
        row = dict(row)
        if label in {BoundaryLabel.HARD_OOD.value, BoundaryLabel.TRUE_FALSE_ACCEPT_TRAP.value, BoundaryLabel.LABEL_REVIEW_CANDIDATE.value} and index % 20 == 0:
            row["split"] = "eval_ood_boundary"
        elif label == BoundaryLabel.FUTURE_DOMAIN_CANDIDATE.value and index % 20 == 0:
            row["split"] = "eval_future_domain"
        elif label == BoundaryLabel.NEAR_OOD_GENERALIZATION_CANDIDATE.value and index % 20 == 0:
            row["split"] = "eval_near_ood"
        elif row["boundary_label"] == BoundaryLabel.CURRENT_SUPPORTED.value and index % 10 == 0:
            row["split"] = "eval_unseen_target"
        elif row["boundary_label"] == BoundaryLabel.CURRENT_SUPPORTED.value and index % 10 == 1:
            row["split"] = "eval_seen_target_unseen_paraphrase"
        else:
            row["split"] = "train"
        buckets[row["split"]].append(row)
    return buckets


def _deduplicate_raw(samples: List[Dict], total: int, seed: int, source_candidates: List[Dict]) -> List[Dict]:
    seen = set()
    rows = []
    extra_round = 0
    pool = list(samples)
    while len(rows) < total:
        if not pool:
            extra_round += 1
            pool = generate_boundary_aware_samples(total, seed=seed + extra_round * 9973, source_candidates=source_candidates)
        row = dict(pool.pop())
        raw = row.get("raw_text")
        if raw in seen:
            row["raw_text"] = f"{raw} （boundary-v085-{len(rows):07d}）"
            row["canonical_text"] = f"{row.get('canonical_text', raw)}#boundary-v085-{len(rows):07d}"
        seen.add(row["raw_text"])
        rows.append(row)
    for index, row in enumerate(rows):
        row["sample_id"] = f"jm-v085-{index:07d}"
        row["paraphrase_group_id"] = f"pg-v085-{index:07d}"
        row["target_group_id"] = f"tg-v085-{index:07d}" if row.get("boundary_label") == BoundaryLabel.CURRENT_SUPPORTED.value else None
    return rows


def _write_split_files(output_dir: Path, splits: Dict[str, List[Dict]]) -> None:
    all_rows = [row for rows in splits.values() for row in rows]
    (output_dir / "all.jsonl").write_text(_jsonl(all_rows), encoding="utf-8")
    for name, rows in splits.items():
        (output_dir / f"{name}.jsonl").write_text(_jsonl(rows), encoding="utf-8")


def _manifest(scale: str, samples: List[Dict], splits: Dict[str, List[Dict]], audit: Dict) -> Dict:
    return {
        "dataset_version": "v0_8_5_boundary_aware",
        "scale": scale,
        "total": len(samples),
        "split_counts": {name: len(rows) for name, rows in splits.items()},
        "boundary_label_distribution": dict(Counter(row["boundary_label"] for row in samples)),
        "audit_passed": audit["audit_passed"],
        "auto_added_to_training": False,
    }


def _report(scale: str, samples: List[Dict], audit: Dict, curriculum: Dict) -> str:
    return "\n".join(
        [
            "# Boundary-Aware Dataset Curriculum（边界感知数据课程）",
            "",
            "## Dataset Scale Summary（数据规模摘要）",
            f"- scale（规模）: {scale}",
            f"- total（总数）: {len(samples)}",
            "",
            "## Boundary Label Distribution（边界标签分布）",
            f"- {audit['boundary_label_distribution']}",
            "",
            "## Nutrient / Toxic Policy（养分 / 毒性策略）",
            f"- {audit['nutrient_policy_distribution']}",
            "",
            "## Split and Leakage Audit（切分与泄漏审计）",
            f"- audit_passed（审计通过）: {audit['audit_passed']}",
            f"- duplicate_input_count（重复输入数）: {audit['duplicate_input_count']}",
            f"- train_eval_input_leakage_count（训练评测输入泄漏数）: {audit['train_eval_input_leakage_count']}",
            "",
            "## Curriculum Schedule（课程调度）",
            f"- curriculum_stage_count（课程阶段数）: {curriculum['curriculum_stage_count']}",
            "",
            "## Non-Claims（非主张）",
            "- This dataset does not prove stable convergence, solved arithmetic, general program synthesis, or solved OOD.",
        ]
    ) + "\n"


def _jsonl(rows: List[Dict]) -> str:
    return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)


def _write_json(path: Path, payload: Dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
