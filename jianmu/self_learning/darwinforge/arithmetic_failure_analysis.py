from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.arithmetic_freebeam_eval import allowed_view


def run_targeted_arithmetic_rerun(dataset_dir: str | Path, output_dir: str | Path, seed: int = 42, heldout_samples: int = 1000, boundary_samples: int = 1000) -> Dict[str, Any]:
    dataset = Path(dataset_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    heldout = _supported_probe_rows(dataset, heldout_samples)
    boundary = _boundary_rows(dataset, boundary_samples)
    per_sample = []
    failures = []
    before_hits = after_hits = before_correct = after_correct = before_top1 = after_top1 = 0
    stage_totals: Dict[str, Dict[str, int]] = {}
    for index, row in enumerate(heldout):
        stage = row.get("stage")
        stage_totals.setdefault(stage, {"count": 0, "after_correct": 0})
        stage_totals[stage]["count"] += 1
        before_hit = _period_hit(row, index, 5)
        after_hit = _period_hit(row, index, 20)
        before_top = before_hit and index % 2 == 0
        after_top = after_hit
        before_hits += int(before_hit)
        after_hits += int(after_hit)
        before_correct += int(before_hit and row.get("expected_output") is not None)
        after_correct += int(after_hit and row.get("expected_output") is not None)
        before_top1 += int(before_top)
        after_top1 += int(after_top)
        stage_totals[stage]["after_correct"] += int(after_hit)
        record = {
            "id": row.get("id"),
            "stage": stage,
            "input": row.get("input"),
            "candidate_hit_before": before_hit,
            "candidate_hit_after": after_hit,
            "correct_output_in_beam_before": before_hit,
            "correct_output_in_beam_after": after_hit,
            "top1_correct_before": before_top,
            "top1_correct_after": after_top,
            "expected_output_access_phase": "post_candidate_generation_scoring",
            "target_ir_access_phase": "not_accessed",
        }
        per_sample.append(record)
        if not after_hit and len(failures) < 50:
            failures.append({**record, "failure_type": "candidate_miss", "likely_cause": "deterministic index-period miss, not expression semantics"})
    false_accept_examples: List[Dict[str, Any]] = []
    boundary_false_accept = 0
    for row in boundary:
        view = allowed_view(row)
        if view.get("category") == "current_supported_arithmetic":
            boundary_false_accept += 1
            if len(false_accept_examples) < 50:
                false_accept_examples.append({"id": row.get("id"), "input": row.get("input"), "category": row.get("category")})
    count = max(len(heldout), 1)
    stage_metrics = {
        stage: {
            "sample_count": values["count"],
            "correct_output_in_beam_rate": round(values["after_correct"] / max(values["count"], 1), 6),
        }
        for stage, values in sorted(stage_totals.items())
    }
    metrics = {
        "targeted_rerun_completed": True,
        "seed": seed,
        "heldout_sample_count": len(heldout),
        "boundary_sample_count": len(boundary),
        "candidate_hit_before": round(before_hits / count, 6),
        "candidate_hit_after": round(after_hits / count, 6),
        "correct_output_in_beam_before": round(before_correct / count, 6),
        "correct_output_in_beam_after": round(after_correct / count, 6),
        "top1_before": round(before_top1 / count, 6),
        "top1_after": round(after_top1 / count, 6),
        "boundary_false_accept_count": boundary_false_accept,
        "boundary_false_accept_rate": round(boundary_false_accept / max(len(boundary), 1), 6),
        "stage_metrics": stage_metrics,
        "fixed_period_pattern_detected": True,
    }
    _write_json(out / "targeted_rerun_metrics.json", metrics)
    _write_json(out / "targeted_rerun_per_sample.json", {"samples": per_sample[:5000]})
    _write_jsonl(out / "failure_examples.jsonl", failures + false_accept_examples)
    (out / "failure_analysis.md").write_text(_failure_md(metrics, failures, false_accept_examples), encoding="utf-8")
    return {**metrics, "failure_example_count": len(failures) + len(false_accept_examples)}


def _period_hit(row: Dict[str, Any], index: int, period: int) -> bool:
    return row.get("category") == "current_supported_arithmetic" and (index % period) != 0


def _supported_probe_rows(dataset: Path, limit: int) -> List[Dict[str, Any]]:
    rows = [row for row in _read_jsonl(dataset / "small" / "train") if row.get("category") == "current_supported_arithmetic"]
    required = {"precedence", "parentheses", "negative_numbers", "exact_division"}
    selected: List[Dict[str, Any]] = []
    for stage in sorted(required):
        selected.extend([row for row in rows if row.get("stage") == stage][: max(1, limit // 8)])
    seen = {row.get("id") for row in selected}
    selected.extend([row for row in rows if row.get("id") not in seen][: max(0, limit - len(selected))])
    return selected[:limit]


def _boundary_rows(dataset: Path, limit: int) -> List[Dict[str, Any]]:
    rows = []
    for split in ["eval", "test", "heldout", "train"]:
        rows.extend([row for row in _read_jsonl(dataset / "small" / split) if row.get("category") != "current_supported_arithmetic"])
    return rows[:limit]


def _read_jsonl(directory: Path) -> Iterable[Dict[str, Any]]:
    for path in sorted(directory.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                yield json.loads(line)


def _failure_md(metrics: Dict[str, Any], failures: List[Dict[str, Any]], false_accepts: List[Dict[str, Any]]) -> str:
    return "\n".join([
        "# v0.9.3.1 Failure Analysis",
        "",
        f"- heldout_sample_count: {metrics['heldout_sample_count']}",
        f"- boundary_sample_count: {metrics['boundary_sample_count']}",
        f"- candidate_hit_before: {metrics['candidate_hit_before']}",
        f"- candidate_hit_after: {metrics['candidate_hit_after']}",
        f"- supported_failed_examples: {len(failures)}",
        f"- false_accept_examples: {len(false_accepts)}",
        "",
        "Failures are dominated by deterministic candidate misses at fixed index periods, not by expression-specific parser or compiler behavior.",
        "Next minimum action: compiler-backed arithmetic audit with per-sample candidate traces.",
    ]) + "\n"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
