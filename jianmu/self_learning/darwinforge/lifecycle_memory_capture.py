from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class LifecycleRuntimeState:
    schema_version: str = "v0.9.0.lifecycle_runtime_state"
    stage_counters: Dict[str, int] = field(default_factory=dict)
    root_status_transitions: Dict[str, int] = field(default_factory=dict)
    necrosis_events: int = 0
    replacement_events: int = 0
    nourishment_events: int = 0
    starvation_events: int = 0
    stage_deltas: List[Dict[str, Any]] = field(default_factory=list)
    rejection_layer_distribution: Dict[str, Any] = field(default_factory=dict)
    accepted_rejected_distribution: Dict[str, int] = field(default_factory=dict)
    state_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["state_hash"] = self.compute_hash(without_hash=True)
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "LifecycleRuntimeState":
        return cls(**{key: payload.get(key) for key in cls.__dataclass_fields__ if key in payload})

    def compute_hash(self, without_hash: bool = False) -> str:
        payload = asdict(self)
        if without_hash:
            payload["state_hash"] = ""
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def capture_lifecycle_runtime_state(training_result: Dict[str, Any], root_colony_state: Dict[str, Any]) -> LifecycleRuntimeState:
    stage_metrics = training_result.get("stage_metrics", [])
    stage_deltas = []
    accepted = rejected = false_accept = false_reject = 0
    for row in stage_metrics:
        before = row.get("before_metrics", {})
        after = row.get("after_metrics", {})
        stage_deltas.append(
            {
                "stage_name": row.get("stage_name"),
                "sample_count": row.get("sample_count", 0),
                "ood_false_accept_delta": round(after.get("overall_ood_false_accept_rate", 0.0) - before.get("overall_ood_false_accept_rate", 0.0), 6),
                "supported_retention_delta": round(after.get("current_supported_retention_rate", 0.0) - before.get("current_supported_retention_rate", 0.0), 6),
            }
        )
        accepted += int(row.get("accepted_as_supported_count", 0))
        rejected += int(row.get("rejected_count", 0))
        false_accept += int(row.get("false_accept_count", 0))
        false_reject += int(row.get("false_reject_count", 0))
    root_status_transitions = {
        "stable": len(root_colony_state.get("stable_roots", [])),
        "nourished": len(root_colony_state.get("nourished_roots", [])),
        "starving": len(root_colony_state.get("starving_roots", [])),
        "necrotic": len(root_colony_state.get("necrotic_roots", [])),
        "replacement": len(root_colony_state.get("replacement_roots", [])),
    }
    state = LifecycleRuntimeState(
        stage_counters={row.get("stage_name", ""): int(row.get("sample_count", 0)) for row in stage_metrics},
        root_status_transitions=root_status_transitions,
        necrosis_events=root_status_transitions["necrotic"],
        replacement_events=root_status_transitions["replacement"],
        nourishment_events=root_status_transitions["nourished"] + root_status_transitions["stable"],
        starvation_events=root_status_transitions["starving"],
        stage_deltas=stage_deltas,
        rejection_layer_distribution=training_result.get("rejection_layer_distribution", {}),
        accepted_rejected_distribution={
            "accepted_as_supported": accepted,
            "rejected": rejected,
            "false_accept": false_accept,
            "false_reject": false_reject,
        },
    )
    return LifecycleRuntimeState.from_dict(state.to_dict())
