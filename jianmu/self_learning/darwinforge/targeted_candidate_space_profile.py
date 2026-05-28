from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


PROFILE_NAME = "v0_9_10_targeted_expanded_candidate_space"


def targeted_candidate_space_profile() -> Dict[str, Any]:
    return {
        "profile_name": PROFILE_NAME,
        "profile_source": "v0.9.9 diagnostic best budget",
        "profile_is_architecture_change": False,
        "profile_is_diagnostic_budget_profile": True,
        "profile_intended_use": "fresh rerun validation",
        "profile_not_claimed_as_default_architecture": True,
        "beam_size": 64,
        "candidate_budget": 512,
        "control_template_budget": "xlarge",
        "root_expansion_budget": "8x",
        "memory_budget": "8x",
    }


def write_targeted_candidate_space_profile(output_records: str | Path) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    profile = targeted_candidate_space_profile()
    (out / "targeted_candidate_space_profile.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return profile

