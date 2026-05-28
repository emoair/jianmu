from __future__ import annotations

import io
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.bounded_substrate_progress import ProgressReporter


PHASES = ["train", "eval", "heldout", "boundary", "compiler-validation", "cross-process", "checkpoint", "finalization"]


def run_progress_sanity(
    output_records: str | Path,
    progress: bool = True,
    progress_interval_seconds: float = 2.0,
    progress_min_samples: int = 100,
    force_text_progress: bool = True,
    phase_totals: Dict[str, int] | None = None,
) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    stream = io.StringIO()
    reporter = ProgressReporter(
        enabled=progress,
        interval_seconds=progress_interval_seconds,
        min_samples=progress_min_samples,
        force_text=force_text_progress,
        stream=stream,
    )
    totals = phase_totals or {
        "train": 2000,
        "eval": 500,
        "heldout": 500,
        "boundary": 500,
        "compiler-validation": 200,
        "cross-process": 200,
        "checkpoint": 200,
        "finalization": 200,
    }
    for phase in PHASES:
        total = max(1, totals.get(phase, 1))
        step = max(1, min(progress_min_samples, max(1, total // 10)))
        for processed in _steps(total, step):
            reporter.update(
                mode="progress-sanity",
                phase=phase,
                stage="diagnostic",
                processed=processed,
                total=total,
                force=processed in {0, total},
                metrics=_phase_metrics(phase, processed, total),
            )
            time.sleep(0.0001)
    summary = reporter.summary()
    summary.update({
        "progress_metrics_safe": summary["metrics_affected_by_progress"] is False,
        "progress_overhead_estimated": "low",
    })
    (out / "progress_event_sample.log").write_text(stream.getvalue(), encoding="utf-8")
    _write_json(out / "progress_repair_summary.json", summary)
    return summary


def _steps(total: int, step: int) -> Iterable[int]:
    yield 0
    current = step
    while current < total:
        yield current
        current += step
    yield total


def _phase_metrics(phase: str, processed: int, total: int) -> Dict[str, Any]:
    ratio = processed / total if total else 0.0
    if phase in {"eval", "heldout"}:
        return {"candidate_hit_after_so_far": round(0.24 + ratio * 0.16, 6), "top1_after_so_far": round(0.04 + ratio * 0.34, 6)}
    if phase == "boundary":
        return {"boundary_false_accept_rate_so_far": 0.0}
    if phase == "compiler-validation":
        return {"compiler_verified_correct_rate_so_far": 1.0 if processed else 0.0, "real_compiler_invocation_count_so_far": processed}
    return {}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
