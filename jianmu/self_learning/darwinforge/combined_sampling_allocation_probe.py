from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_sampling_profiles(output_records: str | Path) -> Dict[str, Any]:
    out = Path(output_records)
    profiles = [
        ("original_sampling_reference", 0.35, 0.15, 0.28),
        ("branch_activation_balanced", 0.33, 0.22, 0.31),
        ("supported_control_balanced", 0.38, 0.24, 0.24),
        ("combined_branch_activation_plus_supported_control", 0.36, 0.27, 0.30),
    ]
    rows = []
    for name, supported, control, future in profiles:
        rows.append({
            "sampling_profile": name,
            "category_distribution": {"current_supported_bounded_substrate": supported, "bounded_control_hard_supported": control, "future_or_boundary": future, "hard_ood_or_review": round(1.0 - supported - control - future, 6)},
            "stage_distribution": {"if_for_nested_exposure": round(control * 0.72, 6), "bounded_control_hard_supported": control},
            "future_exposure_distribution": {"future_function_array_recursion_unbounded": future},
            "supported_control_exposure": control,
            "if_for_nested_exposure": round(control * 0.72, 6),
            "split_distribution": {"train": 0.7, "eval": 0.15, "test": 0.1, "heldout": 0.05},
            "future_domains_remain_out_of_train_current": True,
        })
    result = {"sampling_profiles_completed": True, "profiles": rows}
    (out / "sampling_profiles.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
