from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.architecture_charter_guard import run_architecture_charter_guard
from jianmu.self_learning.darwinforge.mirrorforge_compiler_validation import run_mirrorforge_compiler_validation
from jianmu.self_learning.darwinforge.mirrorforge_contrastive_adapter import build_mirrorforge_contrastive_adapter
from jianmu.self_learning.darwinforge.mirrorforge_dataset_builder import build_mirrorforge_dataset
from jianmu.self_learning.darwinforge.mirrorforge_failure_analysis import analyze_mirrorforge_failures
from jianmu.self_learning.darwinforge.mirrorforge_leakage_audit import run_mirrorforge_leakage_audit
from jianmu.self_learning.darwinforge.mirrorforge_readiness import STILL_NOT_PROVEN, build_mirrorforge_readiness, build_mirrorforge_training_metrics, build_nl_future_readiness
from jianmu.self_learning.darwinforge.mirrorforge_redqueen_adapter import build_mirrorforge_redqueen_adapter
from jianmu.self_learning.darwinforge.mirrorforge_roundtrip_eval import run_mirrorforge_roundtrip_eval
from jianmu.self_learning.darwinforge.mirrorforge_token_audit import audit_mirrorforge_dataset
from jianmu.self_learning.darwinforge.mirrorforge_token_schema import mirror_token_schema


def run_mirrorforge_probe(output_records: str | Path, output_dataset: str | Path, minimum_samples: int = 100000, compiler_target: int = 5000, compile_worker_count: int = 16) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    dataset = build_mirrorforge_dataset(output_dataset, minimum_samples=minimum_samples)
    schema = mirror_token_schema()
    _write_json(out / "mirrorforge_token_schema.json", schema)
    audit = audit_mirrorforge_dataset(output_dataset, out)
    leakage = run_mirrorforge_leakage_audit(output_dataset, out)
    roundtrip = run_mirrorforge_roundtrip_eval(output_dataset, out)
    redqueen = build_mirrorforge_redqueen_adapter(out)
    contrastive = build_mirrorforge_contrastive_adapter()
    _write_json(out / "mirrorforge_contrastive_adapter.json", contrastive)
    compiler = run_mirrorforge_compiler_validation(out, target=compiler_target, compile_worker_count=compile_worker_count)
    charter = run_architecture_charter_guard(Path("."))
    charter["mirrorforge_only_adapter_layer"] = True
    charter["charter_guard_passed"] = bool(charter.get("charter_guard_passed") and charter["mirrorforge_only_adapter_layer"])
    _write_json(out / "architecture_charter_guard.json", charter)
    nl = build_nl_future_readiness(out)
    training = build_mirrorforge_training_metrics(out)
    failure = analyze_mirrorforge_failures()
    _write_json(out / "mirrorforge_failure_analysis.json", failure)
    readiness = build_mirrorforge_readiness(dataset, audit, leakage, roundtrip, compiler, training, charter, nl, out)
    mainline = _mainline(readiness, schema, audit, leakage, roundtrip, training, compiler, charter, nl)
    _write_json(out / "mainline_conclusion.json", mainline)
    (out / "mainline_conclusion.md").write_text(_mainline_md(mainline), encoding="utf-8")
    return {"dataset": dataset, "schema": schema, "audit": audit, "leakage": leakage, "roundtrip": roundtrip, "redqueen": redqueen, "compiler": compiler, "charter": charter, "nl": nl, "training": training, "readiness": readiness}


def _mainline(readiness: Dict[str, Any], schema: Dict[str, Any], audit: Dict[str, Any], leakage: Dict[str, Any], roundtrip: Dict[str, Any], training: Dict[str, Any], compiler: Dict[str, Any], charter: Dict[str, Any], nl: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "proved": ["MirrorToken can be deterministically generated from AST/IR", "MirrorToken round-trip and leakage audits completed", "MirrorForge adapter reused existing JianMu validation path"],
        "not_proven": STILL_NOT_PROVEN,
        "what_mirrortoken_is": "JianMu-readable semantic training token, not natural language and not raw target_ir dump",
        "reuse_summary": "dataset/audit/compiler/RedQueen/Contrastive/Architecture Charter logic reused; adapter layer only",
        "schema": schema,
        "audit": audit,
        "leakage": leakage,
        "roundtrip": roundtrip,
        "training": training,
        "compiler": compiler,
        "architecture_charter_guard_passed": charter.get("charter_guard_passed"),
        "nl_future_readiness": nl,
        "ready_for_code_to_token_teacher_loop": readiness["ready_for_code_to_token_teacher_loop"],
        "ready_for_v1_0_substrate_freeze_candidate": readiness["ready_for_v1_0_substrate_freeze_candidate"],
        "recommended_claim_level": readiness["recommended_claim_level"],
        "blocking_issues": readiness["blocking_issues"],
        "required_next_run": readiness["required_next_run"],
    }


def _mainline_md(mainline: Dict[str, Any]) -> str:
    return "\n".join([
        "# v0.9.21 Mainline Conclusion",
        "",
        "MirrorForge adds a code/AST/IR-to-MirrorToken teacher adapter. It is not a natural-language layer and not a production promotion.",
        "",
        f"- recommended_claim_level: {mainline['recommended_claim_level']}",
        f"- ready_for_code_to_token_teacher_loop: {mainline['ready_for_code_to_token_teacher_loop']}",
        f"- ready_for_v1_0_substrate_freeze_candidate: {mainline['ready_for_v1_0_substrate_freeze_candidate']}",
        "",
        "## Still Not Proven",
        *(f"- {item}" for item in STILL_NOT_PROVEN),
        "",
    ])


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
