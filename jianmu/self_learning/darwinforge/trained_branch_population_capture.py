from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class TrainedBranchPopulationState:
    schema_version: str = "v0.9.0.trained_branch_population"
    population_id: str = "runtime_branch_population"
    layer_states: List[Dict[str, Any]] = field(default_factory=list)
    candidate_rankers: Dict[str, Any] = field(default_factory=dict)
    branch_neuron_states: List[Dict[str, Any]] = field(default_factory=list)
    semantic_neuron_states: Dict[str, Any] = field(default_factory=dict)
    scoring_weights: Dict[str, Any] = field(default_factory=dict)
    confidence_calibration_state: Dict[str, Any] = field(default_factory=dict)
    support_gate_state: Dict[str, Any] = field(default_factory=dict)
    task_scope_state: Dict[str, Any] = field(default_factory=dict)
    language_target_state: Dict[str, Any] = field(default_factory=dict)
    arithmetic_family_state: Dict[str, Any] = field(default_factory=dict)
    slot_binding_policy_state: Dict[str, Any] = field(default_factory=dict)
    structure_policy_state: Dict[str, Any] = field(default_factory=dict)
    target_builder_state: Dict[str, Any] = field(default_factory=dict)
    learned_boundary_adjustments: Dict[str, Any] = field(default_factory=dict)
    generation_count: int = 0
    seed: int = 42
    state_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["state_hash"] = self.compute_hash(without_hash=True)
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TrainedBranchPopulationState":
        return cls(**{key: payload.get(key) for key in cls.__dataclass_fields__ if key in payload})

    def compute_hash(self, without_hash: bool = False) -> str:
        payload = asdict(self)
        if without_hash:
            payload["state_hash"] = ""
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def capture_trained_branch_population(population: Any, generation_count: int | None = None, seed: int | None = None) -> TrainedBranchPopulationState:
    """Capture a real LayerPreservedPopulation runtime object without changing it."""

    per_layer = getattr(population, "per_layer", {}) or {}
    layers: List[Dict[str, Any]] = []
    neurons: List[Dict[str, Any]] = []
    scoring: Dict[str, Any] = {}
    for layer_name, layer_neurons in sorted(per_layer.items()):
        ranked = sorted(layer_neurons, key=lambda n: getattr(n, "score_value", 0.0), reverse=True)
        layers.append(
            {
                "layer_name": layer_name,
                "neuron_count": len(layer_neurons),
                "options": sorted({getattr(n, "option", "") for n in layer_neurons}),
                "top_score": max((float(getattr(n, "score_value", 0.0)) for n in layer_neurons), default=0.0),
                "top_neuron_ids": [getattr(n, "neuron_id", "") for n in ranked[:5]],
            }
        )
        scoring[layer_name] = {
            "scores": {getattr(n, "neuron_id", ""): float(getattr(n, "score_value", 0.0)) for n in ranked},
            "ranked_neuron_ids": [getattr(n, "neuron_id", "") for n in ranked],
        }
        for rank, neuron in enumerate(ranked):
            neurons.append(
                {
                    "neuron_id": getattr(neuron, "neuron_id", ""),
                    "layer_name": getattr(neuron, "layer_name", layer_name),
                    "option": getattr(neuron, "option", ""),
                    "weights": dict(getattr(neuron, "weights", {}) or {}),
                    "threshold": getattr(neuron, "threshold", 0),
                    "score_value": float(getattr(neuron, "score_value", 0.0)),
                    "mutation_count": getattr(neuron, "mutation_count", 0),
                    "rank_within_layer": rank,
                }
            )
    guarded = getattr(population, "guarded_config", None)
    guarded_dict = guarded.to_dict() if hasattr(guarded, "to_dict") else {}
    state = TrainedBranchPopulationState(
        population_id=f"layer_preserved_population_seed_{seed if seed is not None else getattr(population, 'seed', 42)}",
        layer_states=layers,
        candidate_rankers={"top_k_policy": "runtime_configured", "guarded_branchchain": guarded_dict},
        branch_neuron_states=neurons,
        semantic_neuron_states={"status": "not_separate_runtime_object"},
        scoring_weights=scoring,
        confidence_calibration_state=guarded_dict,
        support_gate_state=_layer_state(layers, "support_gate"),
        task_scope_state=_layer_state(layers, "task_scope"),
        language_target_state=_layer_state(layers, "language_target"),
        arithmetic_family_state=_layer_state(layers, "arithmetic_family"),
        slot_binding_policy_state=_layer_state(layers, "slot_binding_policy"),
        structure_policy_state=_layer_state(layers, "structure_policy"),
        target_builder_state=_layer_state(layers, "target_builder"),
        learned_boundary_adjustments={"source": "boundary_curriculum_runtime_pressure", "available": True},
        generation_count=generation_count if generation_count is not None else getattr(population, "generation", 0),
        seed=seed if seed is not None else getattr(population, "seed", 42),
    )
    return TrainedBranchPopulationState.from_dict(state.to_dict())


def _layer_state(layers: List[Dict[str, Any]], layer_name: str) -> Dict[str, Any]:
    return next((dict(row) for row in layers if row.get("layer_name") == layer_name), {"layer_name": layer_name, "status": "missing"})
