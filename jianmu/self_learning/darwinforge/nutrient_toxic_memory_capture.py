from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class NutrientToxicRuntimeMemory:
    schema_version: str = "v0.9.0.nutrient_toxic_runtime_memory"
    positive_nutrient_events: int = 0
    toxic_events: int = 0
    false_accept_toxic_events: int = 0
    false_reject_toxic_events: int = 0
    future_domain_buffer_events: int = 0
    near_ood_quarantine_events: int = 0
    reward_totals: Dict[str, float] = field(default_factory=dict)
    toxicity_totals: Dict[str, float] = field(default_factory=dict)
    memory_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["memory_hash"] = self.compute_hash(without_hash=True)
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "NutrientToxicRuntimeMemory":
        return cls(**{key: payload.get(key) for key in cls.__dataclass_fields__ if key in payload})

    def compute_hash(self, without_hash: bool = False) -> str:
        payload = asdict(self)
        if without_hash:
            payload["memory_hash"] = ""
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def capture_nutrient_toxic_runtime_memory(training_result: Dict[str, Any]) -> NutrientToxicRuntimeMemory:
    rewards: List[Dict[str, Any]] = training_result.get("reward_records", [])
    positive_events = sum(1 for row in rewards if float(row.get("positive_reward", 0.0) or 0.0) > 0)
    toxic_events = sum(1 for row in rewards if float(row.get("toxicity", 0.0) or 0.0) > 0)
    false_accept_events = sum(1 for row in rewards if "false accept" in str(row.get("toxicity_reason", "")).lower())
    false_reject_events = sum(1 for row in rewards if "false reject" in str(row.get("toxicity_reason", "")).lower())
    future_events = sum(1 for row in rewards if row.get("training_usage") == "future_buffer_only")
    near_events = sum(1 for row in rewards if row.get("training_usage") in {"audit_only", "future_buffer_only"} and row.get("boundary_label") == "near_ood_generalization_candidate")
    by_label_reward: Dict[str, float] = {}
    by_label_toxicity: Dict[str, float] = {}
    for row in rewards:
        label = str(row.get("boundary_label", "unknown"))
        by_label_reward[label] = by_label_reward.get(label, 0.0) + float(row.get("positive_reward", 0.0) or 0.0)
        by_label_toxicity[label] = by_label_toxicity.get(label, 0.0) + float(row.get("toxicity", 0.0) or 0.0)
    state = NutrientToxicRuntimeMemory(
        positive_nutrient_events=positive_events,
        toxic_events=toxic_events,
        false_accept_toxic_events=false_accept_events,
        false_reject_toxic_events=false_reject_events,
        future_domain_buffer_events=future_events,
        near_ood_quarantine_events=near_events,
        reward_totals={key: round(value, 6) for key, value in sorted(by_label_reward.items())},
        toxicity_totals={key: round(value, 6) for key, value in sorted(by_label_toxicity.items())},
    )
    return NutrientToxicRuntimeMemory.from_dict(state.to_dict())
