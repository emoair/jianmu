from __future__ import annotations

from typing import Any, Dict


def recommend_mirrortoken_v2(field_ablation: Dict[str, Any], robustness: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, Any]:
    semantic = next(row for row in metrics["runs"] if row["experiment_group"] == "semantic_mirror_token_only")
    lossless = next(row for row in metrics["runs"] if row["experiment_group"] == "v0_9_21_lossless_reference")
    semantic_close = lossless["top1"] - semantic["top1"] <= 0.01
    return {
        "ready_for_mirrortoken_v2_schema": True,
        "schema_v2_recommendation": "conservative_semantic_v2" if semantic_close else "retain_lossless_teacher_with_semantic_adapter",
        "recommended_v2_changes": [
            "Prefer semantic field names over op-like VAR/INIT markers",
            "Keep explicit loop bound, condition operator, update order, and output variable",
            "Keep lossless normalized form only as offline teacher metadata",
            "Do not expose raw target_ir JSON in token input",
        ],
        "critical_fields_to_keep": field_ablation["most_critical_fields"],
        "robustness_score": robustness["robustness_score"],
    }
