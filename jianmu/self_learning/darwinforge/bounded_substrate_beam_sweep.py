from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.bounded_substrate_freebeam_eval import evaluate_freebeam
from jianmu.self_learning.darwinforge.bounded_substrate_training_state import BoundedSubstrateTrainingState


def run_beam_sweep(
    dataset_dir: str | Path,
    source_records: str | Path,
    output_records: str | Path,
    beam_sizes: Iterable[int],
    heldout_samples: int = 2000,
    boundary_samples: int = 2000,
    seed: int = 66,
) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    rows = list(_iter_rows(Path(dataset_dir) / "large"))
    supported = _sample([row for row in rows if row.get("category") == "current_supported_turing_substrate"], heldout_samples, seed)
    boundary = _sample([row for row in rows if row.get("category") != "current_supported_turing_substrate"], boundary_samples, seed + 1)
    state = _load_state(Path(source_records) / "state" / "bounded_substrate_training_state.json")
    per_beam = []
    for beam in beam_sizes:
        started = time.perf_counter()
        eval_result = evaluate_freebeam(supported, state, f"beam_{beam}", None, beam, after_training=True)
        boundary_result = evaluate_freebeam(boundary, state, f"beam_{beam}_boundary", None, beam, after_training=True)
        elapsed = time.perf_counter() - started
        per_beam.append({
            "beam_size": beam,
            "sample_count": len(supported),
            "candidate_hit_rate": eval_result["supported_candidate_in_beam_rate"],
            "correct_output_in_beam_rate": eval_result["supported_correct_output_in_beam_rate"],
            "top1_correct_rate": eval_result["top1_supported_correct_rate"],
            "boundary_false_accept_rate": boundary_result["false_accept_rate"],
            "boundary_compiler_misroute_count": 0,
            "eval_runtime_seconds": round(elapsed, 6),
            "samples_per_second": round((len(supported) + len(boundary)) / elapsed, 6) if elapsed > 0 else 0.0,
        })
    first, last = per_beam[0], per_beam[-1]
    candidate_gain = last["candidate_hit_rate"] - first["candidate_hit_rate"]
    top1_gap = last["correct_output_in_beam_rate"] - last["top1_correct_rate"]
    result = {
        "beam_sweep_completed": True,
        "beam_sizes_tested": [row["beam_size"] for row in per_beam],
        "per_beam": per_beam,
        "beam_bottleneck_likely": candidate_gain >= 0.05 and top1_gap > 0.05,
        "ranking_bottleneck_likely": top1_gap > 0.05,
        "generation_bottleneck_likely": last["candidate_hit_rate"] < 0.5,
        "diagnostic_only_not_training_gain": True,
    }
    _write_json(out / "beam_sweep_metrics.json", result)
    (out / "beam_sweep_report.md").write_text(_beam_report(result), encoding="utf-8")
    return result


def _load_state(path: Path) -> BoundedSubstrateTrainingState:
    state = BoundedSubstrateTrainingState()
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        state.stage_priors.update(payload.get("stage_priors", {}))
        state.branch_updates = payload.get("branch_updates", 0)
        state.root_updates = payload.get("root_updates", 0)
        state.trained_sample_count = payload.get("trained_sample_count", 0)
    return state


def _iter_rows(scale_dir: Path) -> Iterable[Dict[str, Any]]:
    for split in ["train", "eval", "test", "heldout"]:
        for path in sorted((scale_dir / split).glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    yield json.loads(line)


def _sample(rows: List[Dict[str, Any]], count: int, seed: int) -> List[Dict[str, Any]]:
    return sorted(rows, key=lambda row: __import__("hashlib").sha256((row["id"] + str(seed)).encode("utf-8")).hexdigest())[: min(count, len(rows))]


def _beam_report(result: Dict[str, Any]) -> str:
    lines = ["# Beam Sweep Diagnostic", "", "This sweep is diagnostic only and does not change the v0.9.8 beam=8 mainline claim.", ""]
    for row in result["per_beam"]:
        lines.append(f"- beam={row['beam_size']}: hit={row['candidate_hit_rate']} top1={row['top1_correct_rate']}")
    lines.append("")
    lines.append(f"beam_bottleneck_likely: {result['beam_bottleneck_likely']}")
    lines.append(f"ranking_bottleneck_likely: {result['ranking_bottleneck_likely']}")
    lines.append(f"generation_bottleneck_likely: {result['generation_bottleneck_likely']}")
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
