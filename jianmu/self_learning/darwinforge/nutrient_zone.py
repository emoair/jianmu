from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List


@dataclass
class NutrientZone:
    zone_id: str
    fork_layer: str
    stable_prefix_signature: str
    feature_pattern: Dict
    input_mode: str
    expression_family: str
    structure_policy: str
    slot_binding_policy: str
    source_sample_ids: List[str] = field(default_factory=list)
    created_generation: int = 0
    nutrient_score_history: List[float] = field(default_factory=list)
    toxicity_score_history: List[float] = field(default_factory=list)
    local_prior_state: Dict = field(default_factory=dict)
    promotion_state: str = "local_only"

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def create_zones_from_rescued_paths(rescued_paths: Iterable, router_score_diagnostics: List[Dict], min_samples_per_zone: int = 2) -> List[NutrientZone]:
    """Create Nutrient Zone（养分区） clusters from train rescued paths."""

    diag_by_id = {row.get("sample_id"): row for row in router_score_diagnostics}
    buckets = defaultdict(list)
    for record in rescued_paths:
        payload = record.to_dict() if hasattr(record, "to_dict") else dict(record)
        if payload.get("split", "train") != "train" or not payload.get("rescued_by_subbeam", True):
            continue
        pattern = _feature_pattern(payload, diag_by_id.get(payload.get("sample_id"), {}))
        key = (
            payload.get("fork_layer", ""),
            pattern.get("input_mode"),
            pattern.get("structure_policy"),
            pattern.get("slot_binding_policy"),
            pattern.get("number_bucket"),
            pattern.get("operator_bucket"),
        )
        buckets[key].append((payload, pattern))
    zones = []
    for index, (key, rows) in enumerate(sorted(buckets.items())):
        if len(rows) < min_samples_per_zone:
            continue
        first, pattern = rows[0]
        zone_id = "zone:" + hashlib.sha1(repr(key).encode("utf-8")).hexdigest()[:12]
        zones.append(
            NutrientZone(
                zone_id=zone_id,
                fork_layer=key[0],
                stable_prefix_signature=_stable_prefix_signature(first.get("subbeam_path", [])),
                feature_pattern=pattern,
                input_mode=pattern.get("input_mode", ""),
                expression_family=pattern.get("expression_family", ""),
                structure_policy=pattern.get("structure_policy", ""),
                slot_binding_policy=pattern.get("slot_binding_policy", ""),
                source_sample_ids=sorted({row[0].get("sample_id") for row in rows}),
                created_generation=0,
                local_prior_state={"sample_count": len(rows), "zone_key": list(key)},
            )
        )
    return zones


def summarize_zones(zones: List[NutrientZone]) -> Dict:
    return {
        "nutrient_zone_count": len(zones),
        "avg_samples_per_zone": round(sum(len(zone.source_sample_ids) for zone in zones) / max(len(zones), 1), 4),
        "fork_layer_distribution": dict(Counter(zone.fork_layer for zone in zones)),
        "zone_promotion_state_distribution": dict(Counter(zone.promotion_state for zone in zones)),
    }


def _feature_pattern(payload: Dict, score_diag: Dict) -> Dict:
    sample = payload
    slot = next((option for layer, option in payload.get("subbeam_path", []) if layer == "slot_binding_policy"), "")
    return {
        "input_mode": sample.get("input_mode", ""),
        "expression_family": sample.get("expression_family", ""),
        "structure_policy": sample.get("structure_policy", ""),
        "slot_binding_policy": slot,
        "number_bucket": min(int(sample.get("number_count", 0) or 0), 3),
        "operator_bucket": min(int(sample.get("operator_count", 0) or 0), 2),
        "fork_layer": payload.get("fork_layer", ""),
    }


def _stable_prefix_signature(path: List[List[str]]) -> str:
    prefix = path[:3] if path else []
    return ">".join(f"{layer}={option}" for layer, option in prefix)
