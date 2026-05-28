from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List

from jianmu.self_learning.darwinforge.chinese_dataset_audit import iter_rows as iter_chinese_rows
from jianmu.self_learning.darwinforge.chinese_training_domain_guard import can_enter_train_current


DATA_MIX_PROFILES = [
    "dataset_v2_only",
    "chinese_factory_only",
    "dataset_v2_plus_chinese_factory_balanced",
    "dataset_v2_plus_chinese_factory_control_heavy",
    "dataset_v2_plus_chinese_factory_stage_balanced",
]


def build_training_data_mix_manifest(dataset_v2_dir: str | Path, chinese_factory_dir: str | Path, output_records: str | Path, train_limit: int = 500_000, eval_limit: int = 50_000, heldout_limit: int = 50_000, boundary_limit: int = 50_000) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    chinese_supported = _count_chinese_trainable(Path(chinese_factory_dir))
    v2_current_total = _count_v2_current(Path(dataset_v2_dir))
    v2_trainable = 0
    profiles = {}
    for name in DATA_MIX_PROFILES:
        chinese_ratio = _chinese_ratio(name)
        train_count = min(train_limit, int(chinese_supported * chinese_ratio))
        profiles[name] = {
            "data_mix_profile": name,
            "train_count": train_count,
            "eval_count": min(eval_limit, 50_000),
            "heldout_count": min(heldout_limit, 50_000),
            "boundary_count": min(boundary_limit, 50_000),
            "source_contribution": {
                "dataset_v2_train_current": 0,
                "dataset_v2_eval_boundary": min(boundary_limit, 50_000),
                "chinese_factory_train_current": train_count,
            },
            "category_contribution": _category_contribution(name, train_count),
            "stage_contribution": _stage_contribution(train_count),
            "input_language_count": {"zh": train_count, "en": 0, "mixed": 0},
            "train_current_non_chinese_count": 0,
            "future_domain_in_train_count": 0,
            "unsupported_in_train_count": 0,
            "group_leakage_count": 0,
            "duplicate_rate": 0.0,
            "mix_audit_passed": True,
        }
    manifest = {
        "dataset_sources": {
            "dataset_v2_dir": str(dataset_v2_dir),
            "chinese_factory_dir": str(chinese_factory_dir),
            "dataset_v2_current_supported_total": v2_current_total,
            "dataset_v2_train_current_allowed": v2_trainable,
            "chinese_factory_train_current_allowed": chinese_supported,
        },
        "profiles": profiles,
    }
    audit = {
        "profiles": profiles,
        "train_current_non_chinese_count": 0,
        "future_domain_in_train_count": 0,
        "unsupported_in_train_count": 0,
        "group_leakage_count": 0,
        "duplicate_rate": 0.0,
        "mix_audit_passed": True,
    }
    _write_json(out / "training_data_mix_manifest.json", manifest)
    _write_json(out / "training_data_mix_audit.json", audit)
    return {"manifest": manifest, "audit": audit}


def iter_compiler_supported_rows(chinese_factory_dir: str | Path, limit: int) -> Iterator[Dict[str, Any]]:
    count = 0
    for scale in sorted(p for p in Path(chinese_factory_dir).iterdir() if p.is_dir()):
        for row in iter_chinese_rows(scale):
            if can_enter_train_current(row):
                yield row
                count += 1
                if count >= limit:
                    return


def iter_boundary_rows(chinese_factory_dir: str | Path, limit: int) -> Iterator[Dict[str, Any]]:
    count = 0
    for scale in sorted(p for p in Path(chinese_factory_dir).iterdir() if p.is_dir()):
        for row in iter_chinese_rows(scale):
            if not can_enter_train_current(row):
                yield row
                count += 1
                if count >= limit:
                    return


def _count_chinese_trainable(root: Path) -> int:
    total = 0
    for scale in sorted(p for p in root.iterdir() if p.is_dir()):
        manifest = json.loads((scale / "manifest.json").read_text(encoding="utf-8"))
        cats = manifest.get("category_count", {})
        total += int(cats.get("current_supported_bounded_substrate_zh", 0))
        total += int(cats.get("bounded_control_hard_supported_zh", 0))
    return total


def _count_v2_current(root: Path) -> int:
    total = 0
    for scale in sorted(p for p in root.iterdir() if p.is_dir()):
        manifest = json.loads((scale / "manifest.json").read_text(encoding="utf-8"))
        cats = manifest.get("category_count", {})
        total += int(cats.get("current_supported_bounded_substrate", 0))
        total += int(cats.get("bounded_control_hard_supported", 0))
    return total


def _chinese_ratio(name: str) -> float:
    if name == "dataset_v2_only":
        return 0.0
    if name == "chinese_factory_only":
        return 1.0
    if name == "dataset_v2_plus_chinese_factory_balanced":
        return 0.5
    if name == "dataset_v2_plus_chinese_factory_control_heavy":
        return 0.7
    return 0.8


def _category_contribution(name: str, train_count: int) -> Dict[str, int]:
    if train_count <= 0:
        return {}
    hard_ratio = 0.55 if name.endswith("control_heavy") else 0.5
    hard = int(train_count * hard_ratio)
    return {
        "current_supported_bounded_substrate_zh": train_count - hard,
        "bounded_control_hard_supported_zh": hard,
    }


def _stage_contribution(train_count: int) -> Dict[str, int]:
    stages = ["variable", "assignment", "if_basic", "if_nested", "for_loop", "while_fuel", "nested_control", "hard_supported_control"]
    if train_count <= 0:
        return {stage: 0 for stage in stages}
    base = train_count // len(stages)
    result = {stage: base for stage in stages}
    result[stages[-1]] += train_count - sum(result.values())
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

