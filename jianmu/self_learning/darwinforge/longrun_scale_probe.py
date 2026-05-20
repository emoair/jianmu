from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class LongRunScaleConfig:
    mode: str
    train_limit: Optional[int]
    eval_limit: Optional[int]
    ood_limit: Optional[int]
    beam_size: int
    subbeam_size: int
    generations: int
    cycle_count: int
    max_total_active_roots: int
    max_roots_per_colony: int
    population_per_layer: int = 64
    proposals_per_layer: int = 6
    exploration_quota: int = 2
    stochastic_samples_per_layer: int = 3
    seed: int = 42

    @property
    def scale_label(self) -> str:
        return self.mode

    def to_runtime_config(self) -> Dict:
        payload = dict(self.__dict__)
        payload["scale_label"] = self.mode
        return payload


def longrun_scale_configs(seed: int = 42) -> Dict[str, LongRunScaleConfig]:
    return {
        "large": LongRunScaleConfig("large", 1600, 600, 300, 96, 96, 12, 10, 4096, 128, 48, seed=seed),
        "xlarge": LongRunScaleConfig("xlarge", 3000, 1000, 500, 128, 128, 20, 16, 8192, 256, 64, seed=seed),
        "full": LongRunScaleConfig("full", None, None, None, 160, 160, 24, 20, 12288, 384, 64, seed=seed),
        "longrun": LongRunScaleConfig("longrun", None, None, None, 192, 192, 32, 24, 16384, 512, 64, seed=seed),
    }


def should_skip_longrun(mode: str, bounded_runtime_sec: Optional[int], allow_expensive: bool = False) -> Optional[str]:
    if mode in {"full", "longrun"} and not allow_expensive:
        return f"{mode} skipped by bounded runtime policy（受限运行时间策略跳过 {mode}）"
    if mode == "xlarge" and bounded_runtime_sec is not None and bounded_runtime_sec < 3600:
        return "xlarge skipped because bounded_runtime_sec is below one hour（受限运行时间低于一小时）"
    return None
