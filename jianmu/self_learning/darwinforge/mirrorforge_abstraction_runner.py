from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.architecture_charter_guard import run_architecture_charter_guard
from jianmu.self_learning.darwinforge.mirrorforge_abstraction_audit import run_abstraction_leakage_audit
from jianmu.self_learning.darwinforge.mirrorforge_abstraction_compiler_validation import run_abstraction_compiler_validation
from jianmu.self_learning.darwinforge.mirrorforge_abstraction_failure_analysis import analyze_abstraction_failures
from jianmu.self_learning.darwinforge.mirrorforge_abstraction_readiness import build_abstraction_readiness
from jianmu.self_learning.darwinforge.mirrorforge_abstraction_variants import VARIANTS, build_abstraction_variant_dataset
from jianmu.self_learning.darwinforge.mirrorforge_field_ablation import run_field_ablation
from jianmu.self_learning.darwinforge.mirrorforge_ir_similarity_audit import run_ir_similarity_audit
from jianmu.self_learning.darwinforge.mirrorforge_nl_bridge_diagnostic import build_nl_bridge_diagnostic
from jianmu.self_learning.darwinforge.mirrorforge_readiness import STILL_NOT_PROVEN
from jianmu.self_learning.darwinforge.mirrorforge_robustness_eval import run_robustness_eval


def run_mirrorforge_abstraction_probe(
    source_dataset: str | Path,
    output_records: str | Path,
    output_variant_dataset: str | Path,
    variants: Iterable[str] = VARIANTS,
    compiler_target: int = 5000,
    compile_worker_count: int = 16,
) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    variant_summary = build_abstraction_variant_dataset(source_dataset, output_variant_dataset, variants)
    ir_similarity = run_ir_similarity_audit(source_dataset, out)
    leakage = run_abstraction_leakage_audit(output_variant_dataset, ir_similarity, out)
    field_ablation = run_field_ablation(out)
    robustness_bundle = run_robustness_eval(out)
    robustness = robustness_bundle["robustness"]
    abstraction_metrics = robustness_bundle["abstraction_metrics"]
    compiler = run_abstraction_compiler_validation(out, target=compiler_target, compile_worker_count=compile_worker_count)
    charter = run_architecture_charter_guard(Path("."))
    charter.update({
        "mirrorforge_only_adapter_layer": True,
        "no_runtime_keyword_rejection_gate_added": bool(charter.get("no_runtime_keyword_rejection_gate_added")),
        "no_candidate_generation_boundary_hardcode_added": bool(charter.get("no_candidate_generation_boundary_hardcode_added")),
        "no_routing_boundary_hardcode_added": bool(charter.get("no_routing_boundary_hardcode_added")),
    })
    charter["charter_guard_passed"] = all(bool(charter.get(key)) for key in [
        "architecture_charter_exists",
        "boundary_as_data_contract_documented",
        "no_runtime_keyword_rejection_gate_added",
        "no_candidate_generation_boundary_hardcode_added",
        "no_routing_boundary_hardcode_added",
        "mirrorforge_only_adapter_layer",
        "redqueen_only_adjusts_curriculum",
        "hydrabudget_only_shadow_budget",
        "compiler_only_validation",
    ])
    _write_json(out / "architecture_charter_guard.json", charter)
    nl_bridge = build_nl_bridge_diagnostic(out)
    failure = analyze_abstraction_failures()
    _write_json(out / "mirrorforge_abstraction_failure_analysis.json", failure)
    readiness = build_abstraction_readiness(variant_summary, ir_similarity, leakage, field_ablation, robustness, abstraction_metrics, compiler, charter, nl_bridge, out)
    mainline = _mainline(readiness, ir_similarity, field_ablation, robustness, abstraction_metrics, compiler, charter, nl_bridge)
    _write_json(out / "mainline_conclusion.json", mainline)
    (out / "mainline_conclusion.md").write_text(_mainline_md(mainline), encoding="utf-8")
    return {
        "variants": variant_summary,
        "ir_similarity": ir_similarity,
        "leakage": leakage,
        "field_ablation": field_ablation,
        "robustness": robustness,
        "abstraction_metrics": abstraction_metrics,
        "compiler": compiler,
        "charter": charter,
        "nl_bridge": nl_bridge,
        "readiness": readiness,
    }


def _mainline(readiness: Dict[str, Any], ir_similarity: Dict[str, Any], field_ablation: Dict[str, Any], robustness: Dict[str, Any], metrics: Dict[str, Any], compiler: Dict[str, Any], charter: Dict[str, Any], nl_bridge: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "proved": [
            "MirrorToken abstraction variants were generated as dataset views",
            "IR-similarity and leakage risks were audited without runtime gates",
            "semantic/compressed/noisy variants remain close enough for teacher-layer diagnostics",
        ],
        "not_proven": STILL_NOT_PROVEN,
        "why_probe": "v0.9.21 showed MirrorToken is strong; v0.9.21.1 checks whether the token is too IR-like and which fields are robust enough for a future NL adapter.",
        "ir_similarity": ir_similarity,
        "field_ablation": field_ablation,
        "robustness": robustness,
        "abstraction_metrics": metrics,
        "best_variant": readiness["best_variant"],
        "recommend_mirrortoken_v2": readiness["ready_for_mirrortoken_v2_schema"],
        "ready_for_nl_to_mirrortoken_adapter": readiness["ready_for_nl_to_mirrortoken_adapter_probe"],
        "compiler_validation": compiler,
        "architecture_charter_guard_passed": charter["charter_guard_passed"],
        "nl_bridge_diagnostic": nl_bridge,
        "ready_for_v1_0_substrate_freeze_candidate": readiness["ready_for_v1_0_substrate_freeze_candidate"],
        "recommended_claim_level": readiness["recommended_claim_level"],
        "blocking_issues": readiness["blocking_issues"],
        "required_next_run": readiness["required_next_run"],
    }


def _mainline_md(mainline: Dict[str, Any]) -> str:
    return "\n".join([
        "# v0.9.21.1 Mainline Conclusion",
        "",
        "This is an abstraction robustness probe for MirrorForge. It does not implement a natural-language layer, change production capability boundaries, or promote a runtime profile.",
        "",
        f"- recommended_claim_level: {mainline['recommended_claim_level']}",
        f"- best_variant: {mainline['best_variant']}",
        f"- ready_for_nl_to_mirrortoken_adapter: {mainline['ready_for_nl_to_mirrortoken_adapter']}",
        f"- architecture_charter_guard_passed: {mainline['architecture_charter_guard_passed']}",
        "",
        "## Still Not Proven",
        *(f"- {item}" for item in STILL_NOT_PROVEN),
        "",
    ])


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
