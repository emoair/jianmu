from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


DATASET_FILES = {
    "near_ood_generalization_candidate": "supported_expansion_candidates.jsonl",
    "future_domain_candidate": "future_domain_candidates.jsonl",
    "true_false_accept": "true_false_accept_cases.jsonl",
    "hard_ood": "hard_ood_cases.jsonl",
    "label_too_strict": "label_review_cases.jsonl",
    "unknown": "unknown_cases.jsonl",
}


def write_ood_candidate_datasets(records: List[Dict], output_dir: str | Path) -> Dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    grouped = {label: [] for label in DATASET_FILES}
    for row in records:
        label = row.get("boundary_label", "unknown")
        grouped.setdefault(label, []).append(_dataset_row(row))
    files = {}
    counts = {}
    for label, filename in DATASET_FILES.items():
        path = output_dir / filename
        rows = grouped.get(label, [])
        path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
        files[label] = str(path)
        counts[label] = len(rows)
    manifest = {
        "dataset_version": "v0_8_4_ood_boundary_candidates",
        "auto_added_to_training": False,
        "files": files,
        "counts": counts,
        "total_records": sum(counts.values()),
    }
    (output_dir / "dataset_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "dataset_report.md").write_text(_dataset_report(manifest), encoding="utf-8")
    return {**manifest, "manifest_path": str(output_dir / "dataset_manifest.json"), "report_path": str(output_dir / "dataset_report.md")}


def candidate_counts(records: Iterable[Dict]) -> Dict:
    counts = Counter(row.get("boundary_label", "unknown") for row in records)
    return {
        "supported_expansion_candidates_count": counts.get("near_ood_generalization_candidate", 0),
        "future_domain_candidates_count": counts.get("future_domain_candidate", 0),
        "true_false_accept_cases_count": counts.get("true_false_accept", 0),
        "label_review_cases_count": counts.get("label_too_strict", 0),
    }


def _dataset_row(row: Dict) -> Dict:
    return {
        "source_version": row.get("source_version"),
        "sample_id": row.get("sample_id"),
        "raw_text": row.get("raw_text"),
        "canonical_text": row.get("canonical_text"),
        "boundary_label": row.get("boundary_label"),
        "recommended_action": row.get("recommended_action"),
        "reason": row.get("reason"),
        "original_ood_class": row.get("original_ood_class"),
        "original_false_accept_reason": row.get("original_false_accept_reason"),
    }


def _dataset_report(manifest: Dict) -> str:
    lines = [
        "# OOD Candidate Datasets（分布外候选数据集）",
        "",
        "These files are audit candidates only. They are not automatically added to training.",
        "",
        "## Counts（数量）",
    ]
    for label, count in manifest["counts"].items():
        lines.append(f"- {label}: {count}")
    lines.extend(
        [
            "",
            "## Non-Claims（非主张）",
            "- Near-OOD candidates are not treated as supported success.",
            "- True false accept cases are not treated as generalization.",
        ]
    )
    return "\n".join(lines) + "\n"
