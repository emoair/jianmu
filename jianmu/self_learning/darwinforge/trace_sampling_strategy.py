from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

from jianmu.self_learning.darwinforge.human_review_pack_schema import HumanReviewPackConfig


def load_policy_trace_rows(source_trace_pack: str | Path) -> List[Dict[str, object]]:
    pack = Path(source_trace_pack)
    rows: List[Dict[str, object]] = []
    for path in sorted(pack.glob("policy_path_trace_*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    row["_trace_shard"] = path.name
                    rows.append(row)
    return rows


def select_review_samples(source_trace_pack: str | Path, output_records: str | Path, config: HumanReviewPackConfig) -> List[Dict[str, object]]:
    rows = load_policy_trace_rows(source_trace_pack)
    rng = random.Random(config.seed)
    by_policy: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_policy[str(row.get("policy"))].append(row)
    selected: List[Dict[str, object]] = []
    for policy, target in config.policy_targets().items():
        bucket = list(by_policy.get(policy, []))
        rng.shuffle(bucket)
        for row in bucket[:target]:
            selected.append(_sample_row(row, len(selected), "stratified_policy_ir_kind_pass_shard_hash"))
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "review_sample_manifest.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in selected), encoding="utf-8")
    return selected


def select_replay_samples(source_trace_pack: str | Path, output_records: str | Path, config: HumanReviewPackConfig) -> List[Dict[str, object]]:
    rows = load_policy_trace_rows(source_trace_pack)
    rng = random.Random(config.seed + 1)
    by_policy: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_policy[str(row.get("policy"))].append(row)
    selected: List[Dict[str, object]] = []
    per_policy = max(1, config.replay_validation_samples // max(1, len(config.policy_targets())))
    for policy in config.policy_targets():
        bucket = list(by_policy.get(policy, []))
        rng.shuffle(bucket)
        for row in bucket[:per_policy]:
            selected.append(_sample_row(row, len(selected), "replay_validation_stratified"))
    if len(selected) < config.replay_validation_samples:
        used = {row["source_trace_id"] for row in selected}
        rest = [row for row in rows if row.get("sample_id") not in used]
        rng.shuffle(rest)
        for row in rest[: config.replay_validation_samples - len(selected)]:
            selected.append(_sample_row(row, len(selected), "replay_validation_fill"))
    return selected[: config.replay_validation_samples]


def _sample_row(row: Dict[str, object], index: int, reason: str) -> Dict[str, object]:
    return {
        "review_sample_id": f"review_{index:05d}",
        "source_trace_id": str(row.get("sample_id")),
        "policy": str(row.get("policy")),
        "ir_kind": str(row.get("ir_kind")),
        "builder": str(row.get("builder")),
        "emitter": str(row.get("emitter")),
        "source_sha256": str(row.get("source_sha256")),
        "expected_stdout": str(row.get("expected_stdout")),
        "actual_stdout": str(row.get("actual_stdout")),
        "original_passed": bool(row.get("passed")),
        "selected_reason": reason,
        "source_trace_shard": str(row.get("_trace_shard", "")),
        "compile_invocation_id": str(row.get("compile_invocation_id", "")),
    }

