from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class TrainedRootColonyState:
    schema_version: str = "v0.9.0.trained_root_colony"
    colony_count: int = 0
    root_count: int = 0
    colonies: List[Dict[str, Any]] = field(default_factory=list)
    active_roots: List[Dict[str, Any]] = field(default_factory=list)
    nourished_roots: List[Dict[str, Any]] = field(default_factory=list)
    stable_roots: List[Dict[str, Any]] = field(default_factory=list)
    starving_roots: List[Dict[str, Any]] = field(default_factory=list)
    necrotic_roots: List[Dict[str, Any]] = field(default_factory=list)
    replacement_roots: List[Dict[str, Any]] = field(default_factory=list)
    quarantine_buffer: List[Dict[str, Any]] = field(default_factory=list)
    future_domain_buffer: List[Dict[str, Any]] = field(default_factory=list)
    near_ood_candidate_buffer: List[Dict[str, Any]] = field(default_factory=list)
    colony_memory: Dict[str, Any] = field(default_factory=dict)
    promotion_shadow_state: Dict[str, Any] = field(default_factory=dict)
    resource_budget_state: Dict[str, Any] = field(default_factory=dict)
    seed: int = 42
    state_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["state_hash"] = self.compute_hash(without_hash=True)
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TrainedRootColonyState":
        return cls(**{key: payload.get(key) for key in cls.__dataclass_fields__ if key in payload})

    def compute_hash(self, without_hash: bool = False) -> str:
        payload = asdict(self)
        if without_hash:
            payload["state_hash"] = ""
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def capture_trained_root_colonies(
    colonies: List[Any],
    quarantine_buffer: List[Dict[str, Any]] | None = None,
    future_domain_buffer: List[Dict[str, Any]] | None = None,
    near_ood_candidate_buffer: List[Dict[str, Any]] | None = None,
    seed: int = 42,
) -> TrainedRootColonyState:
    serialized_colonies = [colony.to_dict() if hasattr(colony, "to_dict") else dict(colony) for colony in colonies]
    tips = []
    for colony in colonies:
        for tip in getattr(colony, "root_tips", []) or []:
            tips.append(tip.to_dict() if hasattr(tip, "to_dict") else dict(tip))
    state = TrainedRootColonyState(
        colony_count=len(colonies),
        root_count=len(tips),
        colonies=serialized_colonies,
        active_roots=[tip for tip in tips if tip.get("state") not in {"necrotic_archived"}],
        nourished_roots=[tip for tip in tips if tip.get("state") == "nourished"],
        stable_roots=[tip for tip in tips if tip.get("state") == "stable"],
        starving_roots=[tip for tip in tips if tip.get("state") == "starving"],
        necrotic_roots=[tip for tip in tips if tip.get("state") == "necrotic_archived"],
        replacement_roots=[tip for tip in tips if tip.get("state") == "replacement"],
        quarantine_buffer=quarantine_buffer or [],
        future_domain_buffer=future_domain_buffer or [],
        near_ood_candidate_buffer=near_ood_candidate_buffer or [],
        colony_memory={
            "colony_stability_scores": {getattr(colony, "colony_id", ""): getattr(colony, "colony_stability_score", 0.0) for colony in colonies},
            "toxicity_scores": {getattr(colony, "colony_id", ""): getattr(colony, "toxicity_score", 0.0) for colony in colonies},
        },
        promotion_shadow_state={"real_promotion_enabled": False, "promotion_state_distribution": _promotion_distribution(colonies)},
        resource_budget_state={"local_resource_budgets": {getattr(colony, "colony_id", ""): getattr(colony, "local_resource_budget", 0) for colony in colonies}},
        seed=seed,
    )
    return TrainedRootColonyState.from_dict(state.to_dict())


def _promotion_distribution(colonies: List[Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for colony in colonies:
        key = getattr(colony, "promotion_state", "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts
