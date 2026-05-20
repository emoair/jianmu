from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ColonyScaleStressConfig:
    scale_label: str
    train_limit: Optional[int]
    eval_limit: Optional[int]
    ood_limit: Optional[int]
    beam_size: int
    subbeam_size: int
    generations: int
    cycle_count: int
    max_total_active_roots: int
    max_roots_per_colony: int
    population_per_layer: int = 32
    proposals_per_layer: int = 6
    exploration_quota: int = 2
    stochastic_samples_per_layer: int = 3
    seed: int = 42

    def to_runtime_config(self) -> Dict:
        return dict(self.__dict__)


def colony_scale_configs(seed: int = 42) -> Dict[str, ColonyScaleStressConfig]:
    return {
        "small": ColonyScaleStressConfig("small", 300, 150, 100, 24, 24, 4, 4, 512, 32, 24, seed=seed),
        "medium": ColonyScaleStressConfig("medium", 800, 300, 150, 48, 48, 8, 6, 1024, 64, 32, seed=seed),
        "large": ColonyScaleStressConfig("large", 1600, 600, 300, 96, 96, 12, 10, 4096, 128, 48, seed=seed),
        "full": ColonyScaleStressConfig("full", None, None, None, 128, 128, 20, 16, 8192, 256, 64, seed=seed),
    }


def scales_for_mode(mode: str) -> List[str]:
    if mode == "small":
        return ["small"]
    if mode == "medium":
        return ["small", "medium"]
    if mode == "large":
        return ["small", "medium", "large"]
    return ["small", "medium", "large", "full"]


def new_run_id(scale_label: str) -> str:
    return f"{scale_label}-{uuid.uuid4().hex[:12]}"


def should_skip_scale(scale_label: str, allow_full: bool = False) -> Optional[str]:
    if scale_label == "full" and not allow_full:
        return "full skipped by bounded runtime policy（受限运行时间策略跳过 full）"
    return None
