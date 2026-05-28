from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


ORDERED_PROFILE_NAMES = ["baseline_targeted", "state_10M", "state_30M", "state_100M"]


def build_state_budget_profiles(names: Iterable[str] | None = None) -> List[Dict[str, Any]]:
    selected = list(names) if names else ORDERED_PROFILE_NAMES
    profiles = []
    for name in selected:
        target = _target_units(name)
        profile = _profile(name, target)
        profiles.append(profile)
    return profiles


def write_state_budget_profiles(output_records: str | Path, profiles: List[Dict[str, Any]]) -> None:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "state_budget_profiles.json").write_text(
        json.dumps({"profiles": profiles}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _target_units(name: str) -> int:
    if name == "baseline_targeted":
        return 1_250_000
    if name == "state_10M":
        return 10_000_000
    if name == "state_30M":
        return 30_000_000
    if name == "state_100M":
        return 100_000_000
    if name == "state_300M":
        return 300_000_000
    raise ValueError(f"unknown state budget profile: {name}")


def _profile(name: str, target: int) -> Dict[str, Any]:
    materialization = "fully_materialized" if target <= 10_000_000 else ("compressed_indexed" if target <= 30_000_000 else "lazy_indexed")
    actual = target
    return {
        "profile_name": name,
        "source": "v0.9.10 targeted profile" if name == "baseline_targeted" else "v0.9.11 state budget scale probe",
        "target_state_units": target,
        "actual_state_units_allocated": actual,
        "materialization_level": materialization,
        "estimated_memory_bytes": _estimated_memory(target, materialization),
        "actual_peak_memory_bytes": 0,
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


def _estimated_memory(target: int, materialization: str) -> int:
    bytes_per_unit = {"fully_materialized": 24, "compressed_indexed": 8, "lazy_indexed": 2, "logical_budget_only": 1, "simulated_budget": 1}[materialization]
    return target * bytes_per_unit

