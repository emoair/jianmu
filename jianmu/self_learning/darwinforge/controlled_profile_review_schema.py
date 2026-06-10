from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple


REQUIRED_V1_0_6_FILES: Tuple[str, ...] = (
    "shadow_profile_config.json",
    "dry_run_profile_guard.json",
    "interface_adapter_audit.json",
    "dry_run_execution_metrics.json",
    "dry_run_compiler_accounting.json",
    "dry_run_regression_guard.json",
    "dry_run_rollback_audit.json",
    "production_profile_dry_run_readiness.json",
    "mainline_conclusion.md",
)

STILL_NOT_PROVEN: Tuple[str, ...] = (
    "production function support completed",
    "production array support completed",
    "production recursion support completed",
    "arbitrary project parsing",
    "formal Turing completeness proof",
    "solved program synthesis",
    "production readiness",
    "natural language layer completed",
    "safe real promotion",
    "stable convergence",
    "solved OOD",
    "emergence proven",
)


@dataclass(frozen=True)
class ControlledProfileReviewConfig:
    replay_samples: int = 2000
    replay_minimum_required: int = 1000
    rollback_cycles: int = 100
    samples_per_rollback_cycle: int = 5
    workers: int = 16
    compiler_workers: int = 16
    trace_writer_mode: str = "sharded"
    temp_dir_mode: str = "per_sample"
    accounting_lock: bool = True
    minimum_unique_compile_units: int = 9000
    minimum_source_sha256_unique: int = 9000


def check_v1_0_6_records(source_records: str | Path) -> Dict[str, object]:
    root = Path(source_records)
    missing = [name for name in REQUIRED_V1_0_6_FILES if not (root / name).exists()]
    if not (root / "dry_run_trace_pack").is_dir():
        missing.append("dry_run_trace_pack/")
    return {
        "source_dry_run_records_found": not missing,
        "source_records": str(root),
        "missing_required_files": missing,
    }
