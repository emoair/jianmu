from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional


@dataclass
class ScaleLadderConfig:
    scale: str
    beam_size: int
    subbeam_size: int
    generations: int
    train_limit: int
    eval_limit: int
    ood_limit: int

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


SCALE_LADDER_CONFIGS = {
    "small": ScaleLadderConfig("small", beam_size=24, subbeam_size=24, generations=4, train_limit=300, eval_limit=150, ood_limit=100),
    "medium": ScaleLadderConfig("medium", beam_size=48, subbeam_size=48, generations=8, train_limit=800, eval_limit=300, ood_limit=150),
    "large": ScaleLadderConfig("large", beam_size=96, subbeam_size=96, generations=12, train_limit=1200, eval_limit=500, ood_limit=200),
}


def scale_ladder_configs() -> Dict[str, ScaleLadderConfig]:
    return dict(SCALE_LADDER_CONFIGS)


def run_scale_ladder(
    runner: Callable[[ScaleLadderConfig], Dict],
    levels: Iterable[str] = ("small", "medium", "large"),
    skip_levels: Optional[Iterable[str]] = None,
) -> List[Dict]:
    skipped = set(skip_levels or [])
    rows = []
    for level in levels:
        config = SCALE_LADDER_CONFIGS[level]
        if level in skipped:
            rows.append({**config.to_dict(), "skipped": True, "skip_reason": "not_run_in_bounded_probe"})
            continue
        metrics = runner(config)
        rows.append(
            {
                **config.to_dict(),
                "skipped": False,
                "correct_targetir_in_beam_rate": metrics.get("correct_targetir_in_beam_rate", 0.0),
                "correct_targetir_in_subbeam_rate": metrics.get("correct_targetir_in_subbeam_rate", 0.0),
                "subbeam_rescue_rate": metrics.get("subbeam_rescue_rate", 0.0),
                "candidate_space_failure_rate": metrics.get("candidate_space_failure_rate", 0.0),
                "ood_false_accept_rate": metrics.get("ood_false_accept_rate", 0.0),
                "runtime_seconds": metrics.get("runtime_seconds", 0.0),
            }
        )
    return rows


def summarize_scale_ladder(rows: List[Dict]) -> Dict:
    actual = [row for row in rows if not row.get("skipped")]
    beam_rates = [row.get("correct_targetir_in_beam_rate", 0.0) for row in actual]
    subbeam_rates = [row.get("subbeam_rescue_rate", 0.0) for row in actual]
    scale_limited = _improves(beam_rates) or _improves(subbeam_rates)
    structural = bool(actual) and all(row.get("correct_targetir_in_beam_rate", 0.0) == 0.0 and row.get("subbeam_rescue_rate", 0.0) == 0.0 for row in actual)
    return {
        "scale_ladder_results": rows,
        "scale_limited_likely": scale_limited,
        "structural_failure_likely": structural,
    }


def _improves(values: List[float]) -> bool:
    return len(values) >= 2 and values[-1] > values[0]
