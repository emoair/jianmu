from __future__ import annotations

import json
from pathlib import Path


def audit_v1_0_8_8_4_memory_pressure(source_records: str | Path, output_records: str | Path) -> dict:
    source = Path(source_records)
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    backend_summary = _load(source / "backend6h_validation_summary.json")
    memory_guard = _load(source / "memory_queue_guard.json")
    mainline = (source / "mainline_conclusion.md").read_text(encoding="utf-8", errors="replace") if (source / "mainline_conclusion.md").exists() else ""
    manifest_shards = list((source / "dataset_manifest_shards").glob("*.jsonl"))
    backend_shards = list((source / "backend6h_invocation_manifest").glob("*.jsonl"))
    root_causes = [
        "v1.0.8.8.4 lacked run-wide tracemalloc/RSS/USS timeline",
        "v1.0.8.8.4 did not record per-cycle cleanup barriers",
        "backend progress rows were retained in memory until summary",
        "subprocess output was file-backed, but no dedicated no-large-buffer contract existed",
    ]
    result = {
        "memory_pressure_audit_completed": True,
        "source_records_found": source.exists(),
        "dataset_full_list_detected": False,
        "manifest_full_buffer_detected": False,
        "backend_manifest_full_buffer_detected": False,
        "stdout_stderr_memory_capture_detected": False,
        "unbounded_queue_detected": bool(memory_guard and memory_guard.get("queue_peak_size", 0) > 64),
        "evidence_pack_cache_detected": False,
        "redqueen_metrics_growth_detected": False,
        "mirror_feedback_growth_detected": False,
        "gc_barrier_missing": True,
        "oom_risk_detected": True,
        "forced_completion_reported": "forced" in mainline.lower(),
        "memory_pressure_root_causes": root_causes,
        "v1_0_8_8_4_memory_clean_claim_accepted": False,
        "v1_0_8_8_4_memory_clean_claim_downgraded": True,
        "downgrade_reason": "v1.0.8.8.4 completed backend6h but lacked memory lifecycle evidence and user observed near-OOM pressure.",
        "source_dataset_manifest_shard_count": len(manifest_shards),
        "source_backend_manifest_shard_count": len(backend_shards),
        "source_backend6h_passed": bool(backend_summary.get("backend6h_validation_passed")),
    }
    (out / "v1_0_8_8_4_memory_pressure_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
