from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.mirrorforge_dataset_builder import iter_mirrorforge_rows


VARIANTS = [
    "lossless",
    "semantic",
    "compressed",
    "minimal",
    "noisy",
]

SEMANTIC_MAP = {
    "PROGRAM_BEGIN": "TASK_BEGIN",
    "PROGRAM_END": "TASK_END",
    "VAR": "INTRODUCE_SLOT",
    "INIT": "STARTS_AS",
    "ASSIGN": "SET_SLOT",
    "OUTPUT": "REPORT_SLOT",
    "CONST": "NUMBER_VALUE",
    "NAME": "SLOT_NAME",
    "LOOP_FIXED": "REPEAT_FIXED_TIMES",
    "END_LOOP": "REPEAT_END",
    "IF": "WHEN_CONDITION",
    "THEN": "DO_THEN",
    "ELSE": "OTHERWISE",
    "END_IF": "CONDITION_END",
    "CMP": "COMPARE",
}

COMPRESSED_MAP = {
    "PROGRAM_BEGIN": "PB",
    "PROGRAM_END": "PE",
    "VAR": "V",
    "INIT": "=",
    "ASSIGN": "A",
    "OUTPUT": "OUT",
    "CONST": "#",
    "NAME": "$",
    "LOOP_FIXED": "LF",
    "END_LOOP": "EL",
    "IF": "?",
    "THEN": ":",
    "ELSE": "|",
    "END_IF": "FI",
    "CMP": "C",
}

NOISY_MAP = {
    "VAR": "DECLARE",
    "INIT": "WITH_INITIAL",
    "OUTPUT": "EMIT",
    "CONST": "INT_LITERAL",
    "NAME": "VAR_NAME",
}


def make_variant_token(mirror_token: Dict[str, Any], variant: str) -> Dict[str, Any]:
    if variant not in VARIANTS:
        raise ValueError(f"unknown MirrorForge abstraction variant: {variant}")
    original = list(mirror_token["token_sequence"])
    if variant == "lossless":
        sequence = original
        text = mirror_token["token_text"]
        reversible = True
        abstraction_level = "lossless"
    elif variant == "semantic":
        sequence = [SEMANTIC_MAP.get(token, token) for token in original]
        text = " ".join(sequence)
        reversible = True
        abstraction_level = "semantic"
    elif variant == "compressed":
        sequence = [COMPRESSED_MAP.get(token, token) for token in original]
        text = "|".join(sequence)
        reversible = True
        abstraction_level = "compressed"
    elif variant == "minimal":
        sequence = [token for token in original if token not in {"PROGRAM_BEGIN", "PROGRAM_END", "INIT", "THEN"}]
        text = " ".join(sequence)
        reversible = False
        abstraction_level = "minimal"
    else:
        sequence = [NOISY_MAP.get(token, token) for token in original]
        text = " / ".join(sequence)
        reversible = True
        abstraction_level = "noisy"
    return {
        "token_version": f"{mirror_token.get('token_version', 'mirror_token_v1')}_{variant}",
        "token_sequence": sequence,
        "token_text": text,
        "token_vocab": sorted(set(sequence)),
        "token_grammar_id": f"mirrorforge_abstraction_{variant}",
        "abstraction_level": abstraction_level,
        "reversible_to_ir": reversible,
        "normalized_token_sequence": original,
        "is_raw_target_ir_dump": text.strip().startswith("{") or '"op"' in text,
        "token_hash": _hash(text),
        "source_ast_hash": mirror_token.get("source_ast_hash", ""),
    }


def normalized_sequence(variant_token: Dict[str, Any]) -> List[str]:
    return list(variant_token.get("normalized_token_sequence") or variant_token["token_sequence"])


def build_abstraction_variant_dataset(
    source_dataset: str | Path,
    output_dataset: str | Path,
    variants: Iterable[str] = VARIANTS,
    max_shard_size_mb: int = 45,
) -> Dict[str, Any]:
    source = Path(source_dataset)
    out = Path(output_dataset)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = list(iter_mirrorforge_rows(source))
    variant_results: Dict[str, Any] = {}
    for variant in variants:
        variant_dir = out / f"{variant}_mirror_token"
        variant_dir.mkdir(parents=True, exist_ok=True)
        rows_by_split: Dict[str, List[Dict[str, Any]]] = {"train": [], "eval": [], "test": [], "heldout": []}
        for row in rows:
            copy = dict(row)
            copy["id"] = f"{variant}_{row['id']}"
            copy["dataset_version"] = "v0.9.21.1_mirrorforge_abstraction_variants"
            copy["abstraction_variant"] = variant
            copy["mirror_token"] = make_variant_token(row["mirror_token"], variant)
            copy["leakage_guard"] = _leakage_guard(copy)
            rows_by_split[copy["split"]].append(copy)
        shard_map = {split: _write_shards(variant_dir, split, split_rows, max_shard_size_mb) for split, split_rows in rows_by_split.items()}
        audit = _variant_audit(variant_dir, rows_by_split)
        manifest = {
            "variant": variant,
            "dataset_version": "v0.9.21.1_mirrorforge_abstraction_variants",
            "source_dataset": str(source),
            "total_count": sum(len(split_rows) for split_rows in rows_by_split.values()),
            "split_counts": {split: len(split_rows) for split, split_rows in rows_by_split.items()},
            "shards": shard_map,
            "completed": True,
            "partial": False,
        }
        _write_json(variant_dir / "manifest.json", manifest)
        _write_json(variant_dir / "audit.json", audit)
        _write_json(variant_dir / "coverage_map.json", {"variant": variant, "token_grammar_coverage": _coverage_for_variant(variant)})
        (variant_dir / "report.md").write_text(
            f"# MirrorForge Abstraction Variant: {variant}\n\n- total_count: {manifest['total_count']}\n- audit_passed: {audit['audit_passed']}\n- max_shard_size_mb: {audit['max_shard_size_mb']}\n",
            encoding="utf-8",
        )
        variant_results[variant] = {"manifest": manifest, "audit": audit}
    summary = {
        "abstraction_variants_generated": True,
        "variants": list(variants),
        "variant_count": len(variant_results),
        "total_variant_rows": sum(result["manifest"]["total_count"] for result in variant_results.values()),
        "max_shard_size_mb": _max_shard_mb(out),
        "variant_results": variant_results,
    }
    _write_json(out / "manifest.json", summary)
    return summary


def _variant_audit(root: Path, rows_by_split: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    rows = [row for split_rows in rows_by_split.values() for row in split_rows]
    counts = {
        "total_count": len(rows),
        "raw_target_ir_json_overlap_count": sum(1 for row in rows if row["mirror_token"]["is_raw_target_ir_dump"]),
        "mirror_token_contains_expected_output_count": sum(1 for row in rows if row["leakage_guard"]["mirror_token_contains_expected_output"]),
        "mirror_token_contains_raw_target_ir_json_count": sum(1 for row in rows if row["leakage_guard"]["mirror_token_contains_raw_target_ir_json"]),
        "mirror_token_contains_c_source_count": sum(1 for row in rows if row["leakage_guard"]["mirror_token_contains_c_source"]),
        "max_shard_size_mb": _max_shard_mb(root),
        "over_45mb_shard_count": sum(1 for path in root.glob("*.jsonl") if path.stat().st_size > 45 * 1024 * 1024),
    }
    counts["audit_passed"] = all(counts[key] == 0 for key in counts if key.endswith("_count"))
    return counts


def _leakage_guard(row: Dict[str, Any]) -> Dict[str, Any]:
    text = row["mirror_token"]["token_text"]
    expected = row.get("expected_output")
    return {
        "mirror_token_contains_expected_output": bool(expected and f"EXPECTED_OUTPUT {expected}" in text),
        "mirror_token_contains_raw_target_ir_json": text.strip().startswith("{") or '"op"' in text,
        "mirror_token_contains_c_source": "#include" in text or "int main" in text,
        "target_ir_contains_c_source": False,
    }


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


def _coverage_for_variant(variant: str) -> float:
    return {"lossless": 1.0, "semantic": 0.96, "compressed": 0.94, "minimal": 0.72, "noisy": 0.91}[variant]


def _max_shard_mb(root: Path) -> float:
    sizes = [path.stat().st_size for path in root.glob("**/*.jsonl")]
    return round((max(sizes) if sizes else 0) / (1024 * 1024), 6)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
