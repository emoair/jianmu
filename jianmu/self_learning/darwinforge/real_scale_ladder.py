from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List


@dataclass
class RealScaleConfig:
    scale_label: str
    beam_size: int
    subbeam_size: int
    generations: int
    train_limit: int
    eval_limit: int
    ood_limit: int

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


REAL_SCALE_CONFIGS = {
    "small": RealScaleConfig("small", 24, 24, 4, 300, 150, 100),
    "medium": RealScaleConfig("medium", 48, 48, 8, 800, 300, 150),
    "large": RealScaleConfig("large", 96, 96, 12, 1200, 500, 200),
}


def run_real_scale_ladder(
    runner: Callable[[RealScaleConfig], Dict],
    levels: Iterable[str] = ("small", "medium", "large"),
    skip_levels: Iterable[str] = (),
) -> List[Dict]:
    skipped = set(skip_levels)
    rows = []
    for level in levels:
        config = REAL_SCALE_CONFIGS[level]
        run_id = f"{level}:{uuid.uuid4().hex[:10]}"
        started = time.time()
        if level in skipped:
            rows.append({**config.to_dict(), "run_id": run_id, "skipped": True, "skip_reason": "bounded_runtime_skip", "runtime_seconds": 0.0})
            continue
        metrics = runner(config)
        ended = time.time()
        rows.append(
            {
                **config.to_dict(),
                "run_id": run_id,
                "started_at": round(started, 4),
                "ended_at": round(ended, 4),
                "runtime_seconds": round(ended - started, 4),
                "skipped": False,
                "evaluator_name": metrics.get("evaluator_name", "free_global_beam"),
                "guard_state": metrics.get("guard_state", "ood_guard_applied"),
                "population_state": metrics.get("population_state", "assimilated"),
                "global_correct_targetir_in_beam_rate": metrics.get("global_correct_targetir_in_beam_rate", 0.0),
                "candidate_space_failure_rate": metrics.get("candidate_space_failure_rate", 0.0),
                "seeded_free_subbeam_correct_targetir_rate": metrics.get("seeded_free_subbeam_correct_targetir_rate", 0.0),
                "subbeam_rescue_rate": metrics.get("subbeam_rescue_rate", 0.0),
                "ood_false_accept_rate": metrics.get("ood_false_accept_rate", 0.0),
                "ood_sample_count": metrics.get("ood_sample_count", config.ood_limit),
            }
        )
    return rows


def summarize_real_scale_ladder(rows: List[Dict], before_rate: float = 0.0, after_rate: float = 0.0) -> Dict:
    actual = [row for row in rows if not row.get("skipped")]
    beam_rates = [row.get("global_correct_targetir_in_beam_rate", 0.0) for row in actual]
    rescue_rates = [row.get("subbeam_rescue_rate", 0.0) for row in actual]
    return {
        "scale_ladder_results": rows,
        "scale_limited_likely": _improves(beam_rates) or _improves(rescue_rates),
        "structural_failure_likely": bool(actual) and all(rate == 0.0 for rate in beam_rates) and all(rate == 0.0 for rate in rescue_rates),
        "assimilation_effect_likely": after_rate > before_rate,
    }


def _improves(values: List[float]) -> bool:
    return len(values) >= 2 and values[-1] > values[0]
