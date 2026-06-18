from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.controlled_opt_in_approval_schema import ApprovalGateConfig


def run_evidence_sampling_review(source_records: str | Path, output_records: str | Path, config: ApprovalGateConfig, seed: int = 216) -> Dict[str, Any]:
    source = Path(source_records)
    out = Path(output_records)
    pack = source / "controlled_support_trace_pack"
    positive = _sample_jsonl(pack, "support_candidate_positive_trace_*.jsonl", config.positive_samples)
    negative = _sample_jsonl(pack, "support_candidate_negative_trace_*.jsonl", config.negative_samples)
    negative_pool = _sample_jsonl(pack, "support_candidate_negative_trace_*.jsonl", config.negative_samples + config.unsupported_rejection_samples + config.default_blocking_samples + 10_000)
    rollback = _sample_jsonl(pack, "support_candidate_rollback_trace_*.jsonl", config.rollback_samples)
    policy = _sample_jsonl(pack, "support_candidate_policy_path_trace_*.jsonl", config.policy_path_samples)
    stdout = _sample_jsonl(pack, "support_candidate_stdout_comparison_*.jsonl", config.stdout_samples)
    unsupported = [row for row in negative_pool if "unsupported" in str(row.get("category"))][: config.unsupported_rejection_samples]
    default_blocking = [row for row in negative_pool if "blocking" in str(row.get("category"))][: config.default_blocking_samples]
    manifest_rows = []
    for group, rows in {
        "positive": positive,
        "negative": negative,
        "rollback": rollback,
        "policy_path": policy,
        "stdout": stdout,
        "unsupported_rejection": unsupported,
        "default_blocking": default_blocking,
    }.items():
        for row in rows:
            manifest_rows.append({"group": group, "sample_id": row.get("sample_id"), "sample_hash": _hash(json.dumps(row, sort_keys=True, ensure_ascii=False)), "passed": row.get("passed")})
    _write_jsonl(out / "evidence_sampling_manifest.jsonl", manifest_rows)
    result = {
        "evidence_sampling_completed": True,
        "positive_samples_reviewed": len(positive),
        "negative_samples_reviewed": len(negative),
        "rollback_samples_reviewed": len(rollback),
        "policy_path_samples_reviewed": len(policy),
        "stdout_samples_reviewed": len(stdout),
        "unsupported_rejection_samples_reviewed": len(unsupported),
        "default_blocking_samples_reviewed": len(default_blocking),
        "sample_hashes_valid": all(row.get("sample_hash") for row in manifest_rows),
        "stdout_comparisons_clean": all(row.get("passed") is True for row in stdout),
        "policy_path_clean": all(row.get("builder") and row.get("ir_kind") and row.get("emitter") for row in policy),
        "unsupported_rejections_clean": all(row.get("compile_invoked") is False or row.get("compiler_invoked") is False for row in unsupported),
        "default_blocking_clean": all(row.get("compile_invoked") is False or row.get("compiler_invoked") is False for row in default_blocking),
        "rollback_clean": all(row.get("passed") is True for row in rollback),
    }
    result["evidence_sampling_passed"] = all([
        result["positive_samples_reviewed"] >= min(config.positive_samples, len(positive)),
        result["negative_samples_reviewed"] >= min(config.negative_samples, len(negative)),
        result["rollback_samples_reviewed"] >= min(config.rollback_samples, len(rollback)),
        result["policy_path_samples_reviewed"] >= min(config.policy_path_samples, len(policy)),
        result["stdout_samples_reviewed"] >= min(config.stdout_samples, len(stdout)),
        result["sample_hashes_valid"],
        result["stdout_comparisons_clean"],
        result["policy_path_clean"],
        result["unsupported_rejection_samples_reviewed"] >= min(config.unsupported_rejection_samples, len(unsupported)),
        result["default_blocking_samples_reviewed"] >= min(config.default_blocking_samples, len(default_blocking)),
        result["unsupported_rejections_clean"],
        result["default_blocking_clean"],
        result["rollback_clean"],
    ])
    _write_json(out / "evidence_sampling_review.json", result)
    return result


def _sample_jsonl(root: Path, pattern: str, limit: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in sorted(root.glob(pattern)):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
                    if len(rows) >= limit:
                        return rows
    return rows


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
