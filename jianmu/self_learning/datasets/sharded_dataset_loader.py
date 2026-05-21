from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List


@dataclass(frozen=True)
class ShardedDatasetManifest:
    dataset_name: str
    scale: str
    total_count: int
    split_name: str
    shards: List[Dict]
    created_at: str
    source_version: str

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def load_dataset_split(path_or_manifest: str | Path, split_name: str | None = None, limit: int | None = None, seed: int = 42) -> List[Dict]:
    result = load_dataset_split_with_report(path_or_manifest, split_name=split_name, limit=limit, seed=seed)
    return result["records"]


def load_dataset_split_with_report(path_or_manifest: str | Path, split_name: str | None = None, limit: int | None = None, seed: int = 42) -> Dict:
    path = Path(path_or_manifest)
    if path.suffix == ".json":
        records, shard_report = _load_manifest(path, split_name)
        source_type = "sharded_manifest"
    else:
        if not path.exists():
            raise FileNotFoundError(path)
        records = list(_read_jsonl(path))
        shard_report = {"shard_count": 0, "missing_shard_count": 0, "missing_shards": []}
        source_type = "single_file"
    records = _sample_limit(records, limit=limit, seed=seed)
    duplicate_sample_id_count = _duplicate_count(row.get("sample_id") for row in records)
    return {
        "records": records,
        "loaded_count": len(records),
        "actual_loaded_count": len(records),
        "source_type": source_type,
        "duplicate_sample_id_count": duplicate_sample_id_count,
        **shard_report,
    }


def stream_dataset_split(path_or_manifest: str | Path, split_name: str | None = None) -> Iterator[Dict]:
    path = Path(path_or_manifest)
    if path.suffix == ".json":
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for shard in manifest.get("shards", []):
            shard_path = (path.parent / shard["path"]).resolve()
            if not shard_path.exists():
                raise FileNotFoundError(shard_path)
            yield from _read_jsonl(shard_path)
    else:
        yield from _read_jsonl(path)


def write_sharded_manifest(records: List[Dict], output_dir: str | Path, split_name: str, shard_size: int = 1000) -> Dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    shards = []
    for index in range(0, len(records), shard_size):
        chunk = records[index : index + shard_size]
        shard_id = len(shards)
        rel = f"{split_name}-part-{shard_id:05d}.jsonl"
        path = output_dir / rel
        text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in chunk)
        path.write_text(text, encoding="utf-8")
        shards.append({"shard_id": shard_id, "path": rel, "count": len(chunk), "size_bytes": path.stat().st_size, "sha256": _sha256(path)})
    manifest = {
        "dataset_name": "boundary_aware_dataset",
        "scale": "generated",
        "total_count": len(records),
        "split_name": split_name,
        "shards": shards,
        "created_at": "not_recorded",
        "source_version": "v0.8.6",
    }
    manifest_path = output_dir / f"{split_name}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**manifest, "manifest_path": str(manifest_path)}


def _load_manifest(path: Path, split_name: str | None) -> tuple[List[Dict], Dict]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if split_name and manifest.get("split_name") not in {split_name, None}:
        raise ValueError(f"manifest split {manifest.get('split_name')} does not match requested {split_name}")
    missing = []
    records = []
    for shard in manifest.get("shards", []):
        shard_path = path.parent / shard["path"]
        if not shard_path.exists():
            missing.append(str(shard_path))
            continue
        records.extend(_read_jsonl(shard_path))
    if missing:
        raise FileNotFoundError("; ".join(missing))
    return records, {"shard_count": len(manifest.get("shards", [])), "missing_shard_count": 0, "missing_shards": []}


def _read_jsonl(path: Path) -> Iterable[Dict]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield json.loads(line)


def _sample_limit(records: List[Dict], limit: int | None, seed: int) -> List[Dict]:
    if limit is None or limit >= len(records):
        return records
    rng = random.Random(seed)
    indices = list(range(len(records)))
    rng.shuffle(indices)
    selected = sorted(indices[:limit])
    return [records[i] for i in selected]


def _duplicate_count(values: Iterable[str]) -> int:
    vals = list(values)
    return len(vals) - len(set(vals))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()
