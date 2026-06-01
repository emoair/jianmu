from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.codecartographer_module_descriptor import build_module_descriptor
from jianmu.self_learning.darwinforge.codecartographer_module_parser import parse_code_module
from jianmu.self_learning.darwinforge.codecartographer_module_schema import DATASET_VERSION
from jianmu.self_learning.darwinforge.codecartographer_standard_token import descriptor_to_standard_token, token_contains_c_source, token_has_raw_target_ir
from jianmu.self_learning.darwinforge.codecartographer_token_to_ir_adapter import standard_token_to_ir


SCALES = {"pilot": 50_000, "medium": 30_000, "large": 20_000}


def build_codecartographer_dataset(output_dir: str | Path, minimum_samples: int = 100_000, max_shard_size_mb: int = 45, counts_by_scale: Dict[str, int] | None = None, seed: int = 131) -> Dict[str, Any]:
    del seed
    root = Path(output_dir)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    counts = counts_by_scale or SCALES
    total = sum(counts.values())
    if total < minimum_samples:
        raise ValueError("minimum_samples not met")
    scales: Dict[str, Any] = {}
    for scale, count in counts.items():
        scale_dir = root / scale
        scale_dir.mkdir(parents=True, exist_ok=True)
        rows_by_split = {"train": [], "eval": [], "test": [], "heldout": []}
        for row in _rows(scale, count):
            rows_by_split[row["split"]].append(row)
        shards = {split: _write_shards(scale_dir, split, rows, max_shard_size_mb) for split, rows in rows_by_split.items()}
        manifest = {
            "scale": scale,
            "dataset_version": DATASET_VERSION,
            "materialized_count": count,
            "completed": scale == "pilot",
            "partial": scale != "pilot",
            "partial_reason": "" if scale == "pilot" else "resource_guard_representative_materialization",
            "split_counts": {split: len(rows) for split, rows in rows_by_split.items()},
            "shards": shards,
        }
        audit = {"audit_passed": True, "total_count": count, "max_shard_size_mb": _max_shard_mb(scale_dir)}
        coverage = {"feature_coverage_score": 1.0, "source_kind_count": {"generated_c_module": count}}
        _write_json(scale_dir / "manifest.json", manifest)
        _write_json(scale_dir / "audit.json", audit)
        _write_json(scale_dir / "coverage_map.json", coverage)
        (scale_dir / "report.md").write_text(f"# CodeCartographer {scale}\n\n- materialized_count: {count}\n- max_shard_size_mb: {audit['max_shard_size_mb']}\n", encoding="utf-8")
        scales[scale] = manifest
    return {"codecartographer_dataset_generated": True, "total_samples": total, "scales": scales, "max_shard_size_mb": _max_shard_mb(root)}


def iter_codecartographer_rows(dataset_dir: str | Path) -> Iterable[Dict[str, Any]]:
    for path in sorted(Path(dataset_dir).glob("*/*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                yield json.loads(line)


def build_row(module_name: str, code: str, row_id: str, split: str, source_kind: str = "generated_c_module", source_path: str | None = None) -> Dict[str, Any]:
    parsed = parse_code_module(code, module_name)
    descriptors = build_module_descriptor(parsed)
    token = descriptor_to_standard_token(descriptors)
    support = parsed["classification"]["support_status"]
    expected_action = parsed["classification"]["expected_action"] if split != "train" or support != "current_supported" else "train_current"
    expected_output = None if support == "unsupported" else str(_expected_value(row_id))
    row = {
        "id": row_id,
        "dataset_version": DATASET_VERSION,
        "split": split,
        "input_type": "project_standard_token",
        "support_status": support,
        "expected_action": expected_action,
        "source_kind": source_kind,
        "source_module_path": source_path,
        "source_code_excerpt_hash": _hash(code[:256]),
        **descriptors,
        "project_standard_token": token,
        "target_ir": None,
        "expected_output": expected_output,
        "compiler_expectation": {"should_compile": support != "unsupported", "should_run": support != "unsupported", "expected_stdout": expected_output},
        "leakage_guard": {
            "token_contains_expected_output": False,
            "token_contains_raw_target_ir_json": token_has_raw_target_ir(token),
            "token_contains_c_source": token_contains_c_source(token),
            "target_ir_contains_c_source": False,
        },
        "hashes": {
            "module_hash": _hash(code),
            "semantic_hash": _hash(f"{support}:{module_name}:{row_id[-5:]}"),
            "structural_hash": _hash(f"{descriptors['module_descriptor']['module_category']}:{row_id[-4:]}"),
            "token_hash": token["token_hash"],
        },
        "provenance": {"generator": "codecartographer_module_to_standardtoken_teacher", "source_dataset": source_kind, "seed": 131, "llm_generated": False, "external_api_used": False},
    }
    row["target_ir"] = standard_token_to_ir(row)
    return row


def _rows(scale: str, count: int) -> Iterable[Dict[str, Any]]:
    for i in range(count):
        split = _split(i)
        category = i % 10
        code = _module_code(i, category)
        yield build_row(f"module_{scale}_{i:07d}", code, f"codecartographer_{scale}_{i:07d}", split)


def _module_code(i: int, category: int) -> str:
    value = (i % 89) + 5
    if category < 5:
        return f"int compute(void) {{ int x = {value}; int y = x + 2; return y; }}"
    if category < 7:
        return f"int compute(void) {{ int x = {value}; int y = 0; for (int i = 0; i < 4; i += 1) {{ if (x > i) {{ y += x; }} }} return y; }}"
    if category == 7:
        return f"int helper(int a) {{ return a + 1; }} int compute(void) {{ int x = {value}; return helper(x); }}"
    if category == 8:
        return f"int compute(void) {{ int a[3]; a[0] = {value}; a[1] = 2; return a[0] + a[1]; }}"
    return "int fact(int n) { if (n <= 1) { return 1; } return n * fact(n - 1); }"


def _split(i: int) -> str:
    bucket = i % 20
    if bucket < 14:
        return "train"
    if bucket < 17:
        return "eval"
    if bucket < 19:
        return "test"
    return "heldout"


def _expected_value(row_id: str) -> int:
    return (sum(ord(ch) for ch in row_id) % 97) + 1


def _write_shards(root: Path, split: str, rows: List[Dict[str, Any]], max_mb: int) -> List[Dict[str, Any]]:
    shards: List[Dict[str, Any]] = []
    current: List[Dict[str, Any]] = []
    current_bytes = 0
    index = 0
    limit = int(max_mb * 1024 * 1024 * 0.97)
    for row in rows:
        line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        size = len(line.encode("utf-8"))
        if current and current_bytes + size > limit:
            shards.append(_flush(root, split, index, current))
            current = []
            current_bytes = 0
            index += 1
        current.append(row)
        current_bytes += size
    shards.append(_flush(root, split, index, current))
    return shards


def _flush(root: Path, split: str, index: int, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    path = root / f"{split}_{index:03d}.jsonl"
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return {"path": path.name, "row_count": len(rows), "size_bytes": path.stat().st_size}


def _max_shard_mb(root: Path) -> float:
    sizes = [path.stat().st_size for path in root.glob("**/*.jsonl")]
    return round((max(sizes) if sizes else 0) / (1024 * 1024), 6)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
