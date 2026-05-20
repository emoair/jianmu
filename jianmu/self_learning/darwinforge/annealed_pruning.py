from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class AnnealingState:
    generation: int
    total_generations: int
    annealing_phase: str
    temperature: float
    effective_beam_size: int
    effective_perturbation_scale: float
    pruning_strength: float

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def annealing_schedule(generation: int, total_generations: int, base_beam_size: int, base_perturbation_scale: float) -> AnnealingState:
    progress = generation / max(total_generations - 1, 1)
    if progress < 0.34:
        phase = "early"
        temperature = 1.0
        beam_multiplier = 1.0
        perturb_multiplier = 1.0
        pruning = 0.1
    elif progress < 0.67:
        phase = "middle"
        temperature = 0.6
        beam_multiplier = 0.75
        perturb_multiplier = 0.7
        pruning = 0.4
    else:
        phase = "late"
        temperature = 0.25
        beam_multiplier = 0.5
        perturb_multiplier = 0.35
        pruning = 0.8
    return AnnealingState(
        generation=generation,
        total_generations=total_generations,
        annealing_phase=phase,
        temperature=temperature,
        effective_beam_size=max(1, int(round(base_beam_size * beam_multiplier))),
        effective_perturbation_scale=round(base_perturbation_scale * perturb_multiplier, 4),
        pruning_strength=pruning,
    )
