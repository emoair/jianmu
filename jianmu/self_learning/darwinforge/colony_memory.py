from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List


@dataclass
class ColonyMemory:
    positive_memory: List[Dict] = field(default_factory=list)
    toxic_memory: List[Dict] = field(default_factory=list)
    necrotic_archive: List[Dict] = field(default_factory=list)
    stable_colony_buffer: List[Dict] = field(default_factory=list)
    quarantined_colony_buffer: List[Dict] = field(default_factory=list)

    def to_rows(self) -> List[Dict]:
        rows = []
        for name in ["positive_memory", "toxic_memory", "necrotic_archive", "stable_colony_buffer", "quarantined_colony_buffer"]:
            for item in getattr(self, name):
                rows.append({"memory_type": name, **item})
        return rows


def update_colony_memory(colonies: Iterable, candidates: List[Dict], nutrient_signals: Dict[str, Dict]) -> ColonyMemory:
    memory = ColonyMemory()
    for candidate in candidates:
        signal = nutrient_signals.get(candidate.get("root_id"), {})
        row = {"root_id": candidate.get("root_id"), "sample_id": candidate.get("sample_id"), "zone_id": candidate.get("zone_id"), "nutrient": signal}
        if signal.get("positive_nutrient", 0) > 0:
            memory.positive_memory.append(row)
        if signal.get("toxic_nutrient", 0) > 0:
            memory.toxic_memory.append(row)
    for colony in colonies:
        if colony.toxicity_score > colony.colony_stability_score:
            memory.quarantined_colony_buffer.append({"colony_id": colony.colony_id, "zone_id": colony.zone_id, "toxicity_score": colony.toxicity_score})
        elif colony.colony_stability_score > 0:
            memory.stable_colony_buffer.append({"colony_id": colony.colony_id, "zone_id": colony.zone_id, "stability_score": colony.colony_stability_score})
        for tip in colony.necrotic_archive:
            memory.necrotic_archive.append({"colony_id": colony.colony_id, "root_id": tip.tip_id, "zone_id": colony.zone_id})
    return memory
