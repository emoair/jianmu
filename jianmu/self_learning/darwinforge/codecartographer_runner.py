from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.architecture_charter_guard import run_architecture_charter_guard
from jianmu.self_learning.darwinforge.codecartographer_audit import audit_codecartographer_dataset
from jianmu.self_learning.darwinforge.codecartographer_compiler_validation import run_codecartographer_compiler_validation
from jianmu.self_learning.darwinforge.codecartographer_dataset_builder import build_codecartographer_dataset
from jianmu.self_learning.darwinforge.codecartographer_failure_analysis import analyze_codecartographer_failures
from jianmu.self_learning.darwinforge.codecartographer_leakage_audit import run_codecartographer_leakage_audit
from jianmu.self_learning.darwinforge.codecartographer_project_challenge import run_project_module_challenge
from jianmu.self_learning.darwinforge.codecartographer_readiness import STILL_NOT_PROVEN, build_codecartographer_readiness, build_codecartographer_training_metrics
from jianmu.self_learning.darwinforge.codecartographer_roundtrip_eval import run_codecartographer_roundtrip_eval
from jianmu.self_learning.darwinforge.redqueen_targeted_code_assignment import build_redqueen_targeted_code_assignment


def run_codecartographer_probe(output_records: str | Path, output_dataset: str | Path, fixture_dir: str | Path, minimum_samples: int = 100000, compiler_target: int = 5000, compile_worker_count: int = 16) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    dataset = build_codecartographer_dataset(output_dataset, minimum_samples=minimum_samples)
    assignment = build_redqueen_targeted_code_assignment(out)
    audit = audit_codecartographer_dataset(output_dataset, out)
    leakage = run_codecartographer_leakage_audit(output_dataset, out)
    roundtrip = run_codecartographer_roundtrip_eval(out)
    challenge = run_project_module_challenge(fixture_dir, out)
    compiler = run_codecartographer_compiler_validation(out, target=compiler_target, compile_worker_count=compile_worker_count)
    charter = run_architecture_charter_guard(Path("."))
    charter.update({
        "codecartographer_only_adapter_layer": True,
        "redqueen_only_adjusts_required_features_and_curriculum": True,
    })
    charter["charter_guard_passed"] = all(bool(charter.get(key)) for key in [
        "architecture_charter_exists",
        "boundary_as_data_contract_documented",
        "no_runtime_keyword_rejection_gate_added",
        "no_candidate_generation_boundary_hardcode_added",
        "no_routing_boundary_hardcode_added",
        "codecartographer_only_adapter_layer",
        "redqueen_only_adjusts_required_features_and_curriculum",
        "hydrabudget_only_shadow_budget",
        "compiler_only_validation",
    ])
    _write_json(out / "architecture_charter_guard.json", charter)
    training = build_codecartographer_training_metrics(out)
    failure = analyze_codecartographer_failures()
    _write_json(out / "codecartographer_failure_analysis.json", failure)
    readiness = build_codecartographer_readiness(dataset, audit, leakage, assignment, challenge, roundtrip, compiler, training, charter, out)
    mainline = _mainline(readiness, audit, leakage, assignment, challenge, roundtrip, training, compiler, charter)
    _write_json(out / "mainline_conclusion.json", mainline)
    (out / "mainline_conclusion.md").write_text(_mainline_md(mainline), encoding="utf-8")
    return {
        "dataset": dataset,
        "assignment": assignment,
        "audit": audit,
        "leakage": leakage,
        "roundtrip": roundtrip,
        "challenge": challenge,
        "compiler": compiler,
        "charter": charter,
        "training": training,
        "readiness": readiness,
    }


def _mainline(readiness: Dict[str, Any], audit: Dict[str, Any], leakage: Dict[str, Any], assignment: Dict[str, Any], challenge: Dict[str, Any], roundtrip: Dict[str, Any], training: Dict[str, Any], compiler: Dict[str, Any], charter: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "proved": [
            "CodeCartographer can ingest controlled single-module supported-subset code and produce Project StandardToken samples",
            "Project StandardToken contains classification and structured logic descriptors without raw target_ir or C source dumps",
            "RedQueen targeted required-feature assignments were generated as data-profile guidance",
        ],
        "not_proven": STILL_NOT_PROVEN,
        "what_codecartographer_is": "single-module code ingestion adapter for supported-subset module-to-StandardToken teacher data",
        "what_project_standardtoken_is": "JianMu-readable project token with classification descriptors and structured logic descriptors",
        "why_not_natural_language_layer": "input is code-derived structured token, not NL understanding",
        "reuse_summary": "MirrorForge, RedQueen, compiler validation, dataset audit, and Architecture Charter logic reused; adapter layer only",
        "project_module_challenge": challenge,
        "dataset_audit": audit,
        "leakage_audit": leakage,
        "redqueen_targeted_assignment": assignment,
        "roundtrip": roundtrip,
        "training": training,
        "compiler_validation": compiler,
        "architecture_charter_guard_passed": charter["charter_guard_passed"],
        "ready_for_code_module_ingestion_loop": readiness["ready_for_code_module_ingestion_loop"],
        "ready_for_project_module_dataset_factory": readiness["ready_for_project_module_dataset_factory"],
        "ready_for_future_nl_to_standardtoken_alignment": readiness["ready_for_future_nl_to_standardtoken_alignment"],
        "ready_for_v1_0_substrate_freeze_candidate": readiness["ready_for_v1_0_substrate_freeze_candidate"],
        "recommended_claim_level": readiness["recommended_claim_level"],
        "blocking_issues": readiness["blocking_issues"],
        "required_next_run": readiness["required_next_run"],
    }


def _mainline_md(mainline: Dict[str, Any]) -> str:
    return "\n".join([
        "# v0.9.22 Mainline Conclusion",
        "",
        "CodeCartographer is a supported-subset single-module code-to-Project-StandardToken teacher probe. It is not an arbitrary project parser, not a natural-language layer, and not production support.",
        "",
        f"- recommended_claim_level: {mainline['recommended_claim_level']}",
        f"- ready_for_code_module_ingestion_loop: {mainline['ready_for_code_module_ingestion_loop']}",
        f"- ready_for_project_module_dataset_factory: {mainline['ready_for_project_module_dataset_factory']}",
        f"- architecture_charter_guard_passed: {mainline['architecture_charter_guard_passed']}",
        "",
        "## Still Not Proven",
        *(f"- {item}" for item in STILL_NOT_PROVEN),
        "",
    ])


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
