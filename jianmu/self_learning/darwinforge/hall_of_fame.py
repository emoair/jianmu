from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class HallOfFame:
    best_generation: Optional[int] = None
    best_metrics: Dict = field(default_factory=dict)
    best_population_summary: Dict = field(default_factory=dict)
    best_records_path: Optional[str] = None

    def update(self, generation: int, metrics: Dict, population):
        if self.best_generation is None or _is_better(generation, metrics, self.best_generation, self.best_metrics):
            self.best_generation = generation
            self.best_metrics = dict(metrics)
            self.best_population_summary = population.summary()

    @property
    def best_target_ir_exact_match(self):
        return self.best_metrics.get("target_ir_exact_match_rate", 0.0)

    @property
    def best_mean_fitness(self):
        return self.best_metrics.get("mean_fitness", 0.0)

    def to_dict(self) -> Dict:
        return {
            "best_generation": self.best_generation,
            "best_metrics": self.best_metrics,
            "best_population_summary": self.best_population_summary,
            "best_records_path": self.best_records_path,
        }


def _is_better(generation: int, metrics: Dict, best_generation: int, best: Dict) -> bool:
    current_key = (
        metrics.get("target_ir_exact_match_rate", 0.0),
        metrics.get("mean_fitness", 0.0),
        -metrics.get("missing_layer_rate", 1.0),
        -generation,
    )
    best_key = (
        best.get("target_ir_exact_match_rate", 0.0),
        best.get("mean_fitness", 0.0),
        -best.get("missing_layer_rate", 1.0),
        -best_generation,
    )
    return current_key > best_key

