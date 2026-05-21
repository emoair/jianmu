from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


@dataclass(frozen=True)
class FullRootState:
    schema_version: str = "v0.8.9.full_root_state"
    colonies: List[Dict[str, Any]] = field(default_factory=list)
    roots: List[Dict[str, Any]] = field(default_factory=list)
    root_status: Dict[str, int] = field(default_factory=dict)
    nutrient_memory: Dict[str, Any] = field(default_factory=dict)
    toxic_memory: Dict[str, Any] = field(default_factory=dict)
    colony_memory: Dict[str, Any] = field(default_factory=dict)
    resource_budget_state: Dict[str, Any] = field(default_factory=dict)
    necrosis_queue: List[Dict[str, Any]] = field(default_factory=list)
    replacement_queue: List[Dict[str, Any]] = field(default_factory=list)
    stable_root_buffer: List[Dict[str, Any]] = field(default_factory=list)
    quarantine_buffer: List[Dict[str, Any]] = field(default_factory=list)
    future_domain_buffer: List[Dict[str, Any]] = field(default_factory=list)
    near_ood_candidate_buffer: List[Dict[str, Any]] = field(default_factory=list)
    lifecycle_counters: Dict[str, int] = field(default_factory=dict)
    seed: int = 42
    source_config: Dict[str, Any] = field(default_factory=dict)
    checksum: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["checksum"] = self.state_hash(without_checksum=True)
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "FullRootState":
        data = dict(payload)
        return cls(**{key: data.get(key) for key in cls.__dataclass_fields__ if key in data})

    @classmethod
    def from_available_runtime(cls, seed: int = 42, source_config: Dict[str, Any] | None = None) -> "FullRootState":
        unavailable = {"status": "unavailable", "reason": "trained root colony runtime object not present in v0.8.8 source records"}
        state = cls(
            root_status={"active": 0, "nourished": 0, "stable": 0, "starving": 0, "necrotic": 0, "replacement": 0},
            nutrient_memory=unavailable,
            toxic_memory=unavailable,
            colony_memory=unavailable,
            resource_budget_state=unavailable,
            lifecycle_counters={"available_runtime_root_count": 0},
            seed=seed,
            source_config=source_config or {},
        )
        return cls.from_dict({**asdict(state), "checksum": state.state_hash(without_checksum=True)})

    def state_hash(self, without_checksum: bool = False) -> str:
        payload = asdict(self)
        if without_checksum:
            payload["checksum"] = ""
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
