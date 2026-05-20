from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Dict, List

from jianmu.self_learning.branchchain.branch_neuron import BranchNeuron


@dataclass
class LayerCloneConfig:
    clone_count_per_layer: int = 4
    perturbation_scale: float = 0.15
    perturbation_mode: str = "medium"
    seed: int = 42
    promote_margin: float = 0.05
    keep_best_n_clones: int = 2


@dataclass
class LayerClone:
    clone_id: str
    layer_name: str
    source_layer_name: str
    source_generation: int
    perturbation_scale: float
    perturbation_seed: int
    neurons: List[BranchNeuron] = field(default_factory=list)
    neuron_weights_snapshot: List[Dict] = field(default_factory=list)
    score_summary: Dict = field(default_factory=dict)
    promoted: bool = False
    discarded: bool = False

    def to_dict(self) -> Dict:
        return {
            "clone_id": self.clone_id,
            "layer_name": self.layer_name,
            "source_layer_name": self.source_layer_name,
            "source_generation": self.source_generation,
            "perturbation_scale": self.perturbation_scale,
            "perturbation_seed": self.perturbation_seed,
            "neuron_weights_snapshot": copy.deepcopy(self.neuron_weights_snapshot),
            "score_summary": dict(self.score_summary),
            "promoted": self.promoted,
            "discarded": self.discarded,
        }


def clone_layer_population(base_layer: List[BranchNeuron], layer_name: str, config: LayerCloneConfig, generation: int) -> List[LayerClone]:
    clones: List[LayerClone] = []
    for clone_index in range(config.clone_count_per_layer):
        seed = config.seed + generation * 1009 + clone_index * 37 + sum(ord(ch) for ch in layer_name)
        rng = random.Random(seed)
        neurons = []
        for neuron in base_layer:
            child = neuron.clone(f"{neuron.neuron_id}.clone{clone_index}")
            for key, value in list(child.weights.items()):
                noise = rng.uniform(-1.0, 1.0) * _mode_scale(config.perturbation_mode) * config.perturbation_scale
                child.weights[key] = value + noise
            child.threshold = max(0, min(100, int(round(child.threshold + rng.uniform(-2, 2) * config.perturbation_scale))))
            child.score_value = neuron.score_value
            neurons.append(child)
        clones.append(
            LayerClone(
                clone_id=f"{layer_name}:clone:{generation}:{clone_index}",
                layer_name=layer_name,
                source_layer_name=layer_name,
                source_generation=generation,
                perturbation_scale=config.perturbation_scale,
                perturbation_seed=seed,
                neurons=neurons,
                neuron_weights_snapshot=[{"neuron_id": n.neuron_id, "option": n.option, "weights": copy.deepcopy(n.weights)} for n in neurons],
                score_summary={"mean_score": round(sum(n.score_value for n in neurons) / max(len(neurons), 1), 4)},
            )
        )
    return clones


def promote_clone_to_layer(population, clone: LayerClone, layer_name: str, base_metric: float = 0.0, clone_metric: float = 0.0, promote_margin: float = 0.05) -> bool:
    if clone_metric < base_metric + promote_margin:
        clone.discarded = True
        return False
    population.per_layer[layer_name] = [neuron.clone(neuron.neuron_id.replace(".clone", ".promoted")) for neuron in clone.neurons]
    clone.promoted = True
    clone.score_summary["promotion_base_metric"] = base_metric
    clone.score_summary["promotion_clone_metric"] = clone_metric
    return True


def _mode_scale(mode: str) -> float:
    return {"small": 0.5, "medium": 1.0, "large": 2.0}.get(mode, 1.0)

