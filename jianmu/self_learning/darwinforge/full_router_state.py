from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List

from jianmu.self_learning.branchchain.branch_chain import LAYER_DEFINITIONS


@dataclass(frozen=True)
class FullRouterState:
    schema_version: str = "v0.8.9.full_router_state"
    branch_layers: List[Dict[str, Any]] = field(default_factory=list)
    branch_neuron_weights: Dict[str, Any] = field(default_factory=dict)
    semantic_neuron_weights: Dict[str, Any] = field(default_factory=dict)
    scoring_biases: Dict[str, Any] = field(default_factory=dict)
    ranking_policy_state: Dict[str, Any] = field(default_factory=dict)
    support_gate_state: Dict[str, Any] = field(default_factory=dict)
    task_scope_state: Dict[str, Any] = field(default_factory=dict)
    language_target_state: Dict[str, Any] = field(default_factory=dict)
    arithmetic_family_state: Dict[str, Any] = field(default_factory=dict)
    slot_binding_policy_state: Dict[str, Any] = field(default_factory=dict)
    structure_policy_state: Dict[str, Any] = field(default_factory=dict)
    target_builder_state: Dict[str, Any] = field(default_factory=dict)
    learned_boundary_adjustments: Dict[str, Any] = field(default_factory=dict)
    seed: int = 42
    source_config: Dict[str, Any] = field(default_factory=dict)
    checksum: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["checksum"] = self.state_hash(without_checksum=True)
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "FullRouterState":
        data = dict(payload)
        return cls(**{key: data.get(key) for key in cls.__dataclass_fields__ if key in data})

    @classmethod
    def from_available_runtime(cls, seed: int = 42, source_config: Dict[str, Any] | None = None) -> "FullRouterState":
        layers = [{"layer_name": layer, "options": list(options)} for layer, options in LAYER_DEFINITIONS]
        unavailable = {"status": "unavailable", "reason": "trained runtime object not present in v0.8.8 source records"}
        state = cls(
            branch_layers=layers,
            branch_neuron_weights={"status": "schema_available_but_trained_population_missing"},
            semantic_neuron_weights=unavailable,
            scoring_biases=unavailable,
            ranking_policy_state={"top_k": "available_from_eval_config"},
            support_gate_state={"layer": "support_gate", "status": "schema_available"},
            task_scope_state={"layer": "task_scope", "status": "schema_available"},
            language_target_state={"layer": "language_target", "status": "schema_available"},
            arithmetic_family_state={"layer": "arithmetic_family", "status": "schema_available"},
            slot_binding_policy_state={"layer": "slot_binding_policy", "status": "schema_available"},
            structure_policy_state={"layer": "structure_policy", "status": "schema_available"},
            target_builder_state={"layer": "target_builder", "status": "schema_available"},
            learned_boundary_adjustments=unavailable,
            seed=seed,
            source_config=source_config or {},
        )
        return cls.from_dict({**asdict(state), "checksum": state.state_hash(without_checksum=True)})

    def state_hash(self, without_checksum: bool = False) -> str:
        payload = asdict(self)
        if without_checksum:
            payload["checksum"] = ""
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
