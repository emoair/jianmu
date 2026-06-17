from __future__ import annotations

from typing import Dict, List

from jianmu.self_learning.darwinforge.coverage_expansion_schema import COMPILER_CATEGORIES, COVERAGE_REPLAY_CATEGORIES


def build_coverage_expansion_schedule(targets: Dict[str, int], wall_clock_min_hours: float = 4.0, workers: int = 16, compiler_workers: int = 16) -> Dict[str, object]:
    total = sum(targets.values())
    return {
        "schedule_created": True,
        "wall_clock_min_hours": wall_clock_min_hours,
        "requires_4h_config": wall_clock_min_hours >= 4.0,
        "workers_requested": workers,
        "workers_used": min(workers, compiler_workers, 16),
        "target_counts": targets,
        "target_real_validation_events": total,
        "all_categories_scheduled": set(COVERAGE_REPLAY_CATEGORIES) <= set(targets),
        "compiler_continuation_categories": list(COMPILER_CATEGORIES),
    }


def next_coverage_kind(counters: Dict[str, int], targets: Dict[str, int], index: int, continuation_mode: bool = False) -> str:
    if continuation_mode:
        return COMPILER_CATEGORIES[index % len(COMPILER_CATEGORIES)]
    remaining: List[str] = [kind for kind in targets if counters[kind] < targets[kind]]
    if remaining:
        return remaining[index % len(remaining)]
    return COMPILER_CATEGORIES[index % len(COMPILER_CATEGORIES)]
