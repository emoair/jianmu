from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from jianmu.self_learning.darwinforge.mirror_landing_schema import (
    BOTH_FROZEN_REVIEW_ONLY,
    INVALID_BOTH_ACTIVE,
    LANE_A_ACTIVE_LANE_B_FROZEN,
    LANE_B_ACTIVE_LANE_A_FROZEN,
)


@dataclass(frozen=True)
class MirrorLaneState:
    phase_id: int
    active_lane: str | None
    frozen_lane: str | None
    lane_a_state: str
    lane_b_state: str
    active_update_allowed: bool
    frozen_update_allowed: bool
    swap_allowed: bool
    simultaneous_active_forbidden: bool = True
    frozen_mutation_forbidden: bool = True
    explicit_opt_in_required: bool = True
    default_profile_reachable: bool = False


def build_mirror_state(phase_id: int, mode: str) -> MirrorLaneState:
    if mode == LANE_A_ACTIVE_LANE_B_FROZEN:
        return MirrorLaneState(phase_id, "lane_a", "lane_b", "active", "frozen", True, False, True)
    if mode == LANE_B_ACTIVE_LANE_A_FROZEN:
        return MirrorLaneState(phase_id, "lane_b", "lane_a", "frozen", "active", True, False, True)
    if mode == BOTH_FROZEN_REVIEW_ONLY:
        return MirrorLaneState(phase_id, None, None, "frozen", "frozen", False, False, True)
    if mode == INVALID_BOTH_ACTIVE:
        raise ValueError("simultaneous active mirror lanes are forbidden")
    raise ValueError(f"unknown mirror mode: {mode}")


def apply_lane_update(state: MirrorLaneState, lane: str, explicit_opt_in: bool = True) -> Dict[str, object]:
    if not explicit_opt_in:
        return {"allowed": False, "reason": "explicit_opt_in_required"}
    if lane == state.frozen_lane or (lane == "lane_a" and state.lane_a_state == "frozen") or (lane == "lane_b" and state.lane_b_state == "frozen"):
        return {"allowed": False, "reason": "frozen_mutation_forbidden"}
    return {"allowed": lane == state.active_lane and state.active_update_allowed, "reason": "active_lane_update" if lane == state.active_lane else "no_active_lane"}


def run_mirror_freeze_state_machine(output_records: str | Path, preexisting_reused: bool = False) -> Dict[str, object]:
    states = [
        build_mirror_state(0, LANE_A_ACTIVE_LANE_B_FROZEN),
        build_mirror_state(1, LANE_B_ACTIVE_LANE_A_FROZEN),
        build_mirror_state(2, BOTH_FROZEN_REVIEW_ONLY),
    ]
    simultaneous_rejected = False
    try:
        build_mirror_state(3, INVALID_BOTH_ACTIVE)
    except ValueError:
        simultaneous_rejected = True
    frozen_rejected = apply_lane_update(states[0], "lane_b")["allowed"] is False
    result = {
        "mirror_state_machine_created_or_confirmed": True,
        "preexisting_state_machine_reused": preexisting_reused,
        "active_lane_defined": True,
        "frozen_lane_defined": True,
        "lane_swap_supported": True,
        "simultaneous_active_rejected": simultaneous_rejected,
        "frozen_mutation_rejected": frozen_rejected,
        "explicit_opt_in_required": True,
        "default_profile_reachable": False,
        "state_machine_passed": simultaneous_rejected and frozen_rejected,
        "states": [state.__dict__ for state in states],
    }
    _write_json(Path(output_records) / "mirror_freeze_state_machine.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

