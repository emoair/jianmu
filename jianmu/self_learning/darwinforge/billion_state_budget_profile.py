from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


ORDERED_BILLION_PROFILES = ["state_100M_reference", "state_300M", "state_600M", "state_1B"]
MAX_TARGET_STATE_UNITS = 1_000_000_000


def build_billion_state_profiles(names: Iterable[str] | None = None) -> List[Dict[str, Any]]:
    selected = list(names) if names else ORDERED_BILLION_PROFILES
    profiles = []
    for name in selected:
        target = _target_units(name)
        if target > MAX_TARGET_STATE_UNITS:
            raise ValueError("v0.9.12 caps target_state_units at 1B")
        profiles.append(_profile(name, target))
    return profiles


def write_billion_state_profiles(output_records: str | Path, profiles: List[Dict[str, Any]]) -> None:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "billion_state_budget_profiles.json").write_text(json.dumps({"profiles": profiles}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _target_units(name: str) -> int:
    if name == "state_100M_reference":
        return 100_000_000
    if name == "state_300M":
        return 300_000_000
    if name == "state_600M":
        return 600_000_000
    if name == "state_1B":
        return 1_000_000_000
    if name == "state_1_5B":
        return 1_500_000_000
    raise ValueError(f"unknown billion-state profile: {name}")


def _profile(name: str, target: int) -> Dict[str, Any]:
    materialization = "lazy_indexed"
    actual = target
    return {
        "profile_name": name,
        "source": "v0.9.11 best profile" if name == "state_100M_reference" else "v0.9.12 upper frontier probe",
        "target_state_units": target,
        "actual_state_units_allocated": actual,
        "materialization_level": materialization,
        "estimated_memory_bytes": target * 2,
        "actual_peak_memory_bytes": 0,
        "estimated_disk_bytes": int(target * 0.55),
        "candidate_fragment_bank_units": int(actual * 0.32),
        "control_template_bank_units": int(actual * 0.14),
        "stage_profile_units": int(actual * 0.08),
        "root_expansion_units": int(actual * 0.12),
        "subroot_units": int(actual * 0.08),
        "failure_pattern_memory_units": int(actual * 0.08),
        "nutrient_toxic_memory_units": int(actual * 0.10),
        "routing_scoring_profile_units": int(actual * 0.05),
        "bounded_control_specialization_units": actual - int(actual * 0.97),
        "profile_is_architecture_change": False,
        "profile_is_budget_scale_probe": True,
    }

