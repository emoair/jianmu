from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.mirrorforge_readiness import STILL_NOT_PROVEN
from jianmu.self_learning.darwinforge.mirrorforge_v2_schema_recommendation import recommend_mirrortoken_v2


def build_abstraction_readiness(
    variants: Dict[str, Any],
    ir_similarity: Dict[str, Any],
    leakage: Dict[str, Any],
    field_ablation: Dict[str, Any],
    robustness: Dict[str, Any],
    abstraction_metrics: Dict[str, Any],
    compiler: Dict[str, Any],
    charter: Dict[str, Any],
    nl_bridge: Dict[str, Any],
    output_records: str | Path,
) -> Dict[str, Any]:
    runs = abstraction_metrics["runs"]
    best = max(runs, key=lambda row: row["top1"])
    lossless = next(row for row in runs if row["experiment_group"] == "v0_9_21_lossless_reference")
    semantic = next(row for row in runs if row["experiment_group"] == "semantic_mirror_token_only")
    compressed = next(row for row in runs if row["experiment_group"] == "compressed_mirror_token_only")
    minimal = next(row for row in runs if row["experiment_group"] == "minimal_mirror_token_only")
    noisy = next(row for row in runs if row["experiment_group"] == "noisy_mirror_token_only")
    compiler_clean = compiler.get("compiler_verified_correct_rate", 0.0) >= 0.98 and all(
        compiler.get(key, 0) == 0
        for key in [
            "wrong_stdout_count",
            "timeout_count",
            "permission_error_count",
            "cleanup_failure_count",
            "boundary_compiler_misroute_count",
            "future_domain_compiled_count",
            "recursion_compiled_count",
            "pointer_compiled_count",
            "io_compiled_count",
        ]
    )
    blocking: List[str] = []
    if not variants.get("abstraction_variants_generated"):
        blocking.append("variants_not_generated")
    if not leakage.get("leakage_audit_passed"):
        blocking.append("leakage_audit_failed")
    if not compiler_clean:
        blocking.append("compiler_validation_not_clean")
    if not charter.get("charter_guard_passed"):
        blocking.append("architecture_charter_failed")
    semantic_close = lossless["top1"] - semantic["top1"] <= 0.01
    compressed_close = lossless["top1"] - compressed["top1"] <= 0.012
    minimal_viable = minimal["token_to_ir_success_rate"] >= 0.70 and minimal["top1"] >= 0.85
    noisy_robust = noisy["robustness_score"] >= 0.88 and robustness["robustness_score"] >= 0.90
    v2 = recommend_mirrortoken_v2(field_ablation, robustness, abstraction_metrics)
    if blocking:
        claim = "failed"
    elif semantic_close and compressed_close and noisy_robust:
        claim = "mirrorforge_abstraction_robust_teacher_layer"
    elif lossless["top1"] - semantic["top1"] > 0.02:
        claim = "mirrorforge_lossless_teacher_strong_but_abstraction_needed"
    else:
        claim = "mirrorforge_abstraction_mixed_needs_schema_v2"
    result = {
        "abstraction_probe_completed": not blocking,
        "abstraction_variants_generated": variants["abstraction_variants_generated"],
        "ir_similarity_audit_completed": ir_similarity["ir_similarity_audit_completed"],
        "leakage_audit_passed": leakage["leakage_audit_passed"],
        "field_ablation_completed": field_ablation["field_ablation_completed"],
        "perturbation_robustness_completed": robustness["perturbation_robustness_completed"],
        "training_eval_completed": abstraction_metrics["training_eval_completed"],
        "compiler_validation_clean": compiler_clean,
        "best_variant": best["variant_name"],
        "best_experiment_group": best["experiment_group"],
        "best_top1": best["top1"],
        "best_candidate_miss": best["candidate_miss"],
        "v0_9_21_reference_top1": lossless["top1"],
        "v0_9_21_reference_candidate_miss": lossless["candidate_miss"],
        "lossless_outperforms_all": lossless["top1"] >= max(row["top1"] for row in runs if row is not lossless),
        "semantic_close_to_lossless": semantic_close,
        "compressed_close_to_lossless": compressed_close,
        "minimal_viable": minimal_viable,
        "noisy_robust": noisy_robust,
        "critical_fields_identified": bool(field_ablation["most_critical_fields"]),
        "fields_too_ir_like_identified": bool(field_ablation["fields_too_ir_like"]),
        "ready_for_mirrortoken_v2_schema": v2["ready_for_mirrortoken_v2_schema"],
        "ready_for_nl_to_mirrortoken_adapter_probe": nl_bridge["ready_for_nl_to_mirrortoken_adapter_probe"],
        "ready_for_v1_0_substrate_freeze_candidate": not blocking and best["top1"] >= 0.917,
        "recommended_claim_level": claim,
        "blocking_issues": blocking,
        "required_next_run": "MirrorToken v2 semantic schema review and NL-to-MirrorToken adapter probe; no real promotion",
        "schema_v2_recommendation": v2,
        "still_not_proven": STILL_NOT_PROVEN,
    }
    _write_json(Path(output_records) / "mirrorforge_abstraction_readiness.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
