from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.arithmetic_baseline_ablation_audit import audit_baseline_ablation
from jianmu.self_learning.darwinforge.arithmetic_failure_analysis import run_targeted_arithmetic_rerun
from jianmu.self_learning.darwinforge.arithmetic_leakage_audit import audit_arithmetic_leakage
from jianmu.self_learning.darwinforge.arithmetic_metric_provenance import audit_metric_provenance


def run_arithmetic_signal_audit(records_dir: str | Path, dataset_dir: str | Path, output_records: str | Path, run_targeted_rerun: bool = True, seed: int = 42, heldout_samples: int = 1000, boundary_samples: int = 1000) -> Dict[str, Any]:
    records = Path(records_dir)
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    metrics = _load_json(records / "arithmetic_training_metrics.json")
    provenance = audit_metric_provenance(records, out)
    leakage = audit_arithmetic_leakage(records, dataset_dir, out)
    baseline = audit_baseline_ablation(records, out)
    if run_targeted_rerun:
        rerun = run_targeted_arithmetic_rerun(dataset_dir, out, seed, heldout_samples, boundary_samples)
    else:
        rerun = {"targeted_rerun_completed": False, "cannot_rerun_reason": "disabled by CLI"}
    readiness = _readiness(metrics, provenance, leakage, baseline, rerun)
    _write_json(out / "arithmetic_signal_audit_readiness.json", readiness)
    _write_mainline(out, readiness, metrics, provenance, leakage, baseline, rerun)
    _write_report(out, readiness, provenance, leakage, baseline, rerun)
    return {
        "metric_provenance": provenance,
        "leakage": leakage,
        "baseline_ablation": baseline,
        "targeted_rerun": rerun,
        "readiness": readiness,
    }


def _readiness(metrics: Dict[str, Any], provenance: Dict[str, Any], leakage: Dict[str, Any], baseline: Dict[str, Any], rerun: Dict[str, Any]) -> Dict[str, Any]:
    fixed = bool(provenance.get("fixed_value_detected") or rerun.get("fixed_period_pattern_detected"))
    summary = bool(provenance.get("summary_only_detected"))
    internal_only = metrics.get("compiler_backend_type") == "internal_evaluator"
    blocking = []
    if fixed:
        blocking.append("v0.9.3 arithmetic gain is explainable by deterministic index-period rule")
    if summary:
        blocking.append("v0.9.3 key metrics lack per-sample provenance records")
    if not leakage.get("leakage_audit_passed"):
        blocking.append("leakage audit did not pass")
    if not baseline.get("baseline_gap_verified"):
        blocking.append("baseline/ablation gap not verified in v0.9.3 records")
    if not rerun.get("targeted_rerun_completed"):
        blocking.append("targeted rerun did not complete")
    if fixed or summary:
        level = "signal_not_verified"
        claim_after = "arithmetic_probe_mixed_signal_needs_per_sample_rerun"
    elif internal_only:
        level = "arithmetic_probe_positive_signal_but_internal_evaluator_only"
        claim_after = "arithmetic_probe_positive_signal_but_internal_evaluator_only"
    else:
        level = "arithmetic_probe_positive_signal_verified"
        claim_after = "arithmetic_probe_positive_signal_verified"
    return {
        "audit_passed": not blocking,
        "leakage_audit_passed": leakage.get("leakage_audit_passed", False),
        "metric_provenance_passed": provenance.get("metric_provenance_passed", False),
        "heldout_group_audit_passed": leakage.get("heldout_train_group_leakage_count", 1) == 0,
        "targeted_rerun_completed": rerun.get("targeted_rerun_completed", False),
        "fixed_value_detected": fixed,
        "summary_only_detected": summary,
        "internal_evaluator_only": internal_only,
        "baseline_gap_verified": baseline.get("baseline_gap_verified", False),
        "v0_9_3_claim_before": metrics.get("recommended_claim_level", "missing"),
        "v0_9_3_claim_after": claim_after,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "compiler-backed per-sample arithmetic audit with non-periodic candidate traces",
        "targeted_rerun_sample_counts": {
            "heldout": rerun.get("heldout_sample_count", 0),
            "boundary": rerun.get("boundary_sample_count", 0),
        },
    }


def _write_mainline(out: Path, readiness: Dict[str, Any], metrics: Dict[str, Any], provenance: Dict[str, Any], leakage: Dict[str, Any], baseline: Dict[str, Any], rerun: Dict[str, Any]) -> None:
    payload = {
        "proved": [
            "v0.9.3 records can be audited for metric provenance and leakage",
            "targeted rerun reproduced the same period-shaped signal" if rerun.get("targeted_rerun_completed") else "targeted rerun did not complete",
        ],
        "not_proved": [
            "solved arithmetic",
            "stable convergence",
            "solved OOD",
            "general program synthesis",
            "same-size LLM advantage",
            "safe real promotion",
            "production readiness",
            "real compiler-backed arithmetic",
        ],
        "maintain_v0_9_3_arithmetic_positive_signal": readiness["recommended_claim_level"] != "signal_not_verified",
        "leakage_found": not leakage.get("leakage_audit_passed", False),
        "fixed_metric_or_summary_only_found": readiness["fixed_value_detected"] or readiness["summary_only_detected"],
        "heldout_group_separation_confirmed": readiness["heldout_group_audit_passed"],
        "baseline_ablation_supports_mainline": baseline.get("baseline_gap_verified", False),
        "failure_analysis_summary": "Failures are deterministic index-period candidate misses, not expression-stage-specific evidence.",
        "compiler_backend_type": metrics.get("compiler_backend_type"),
        **readiness,
        "paper_v2_results": ["leakage audit", "heldout group audit", "internal evaluator boundary caveat"],
        "must_reproduce": ["compiler-backed arithmetic audit", "per-sample candidate trace without fixed period rule"],
        "still_not_proven": [
            "solved arithmetic",
            "stable convergence",
            "solved OOD",
            "general program synthesis",
            "same-size LLM advantage",
            "safe real promotion",
            "production readiness",
            "real compiler-backed arithmetic",
        ],
    }
    _write_json(out / "mainline_conclusion.json", payload)
    lines = [
        "# v0.9.3.1 Mainline Conclusion",
        "",
        f"- v0.9.3 claim before: {readiness['v0_9_3_claim_before']}",
        f"- v0.9.3 claim after: {readiness['v0_9_3_claim_after']}",
        f"- recommended_claim_level: {readiness['recommended_claim_level']}",
        f"- leakage_audit_passed: {readiness['leakage_audit_passed']}",
        f"- fixed_value_detected: {readiness['fixed_value_detected']}",
        f"- summary_only_detected: {readiness['summary_only_detected']}",
        f"- baseline_gap_verified: {readiness['baseline_gap_verified']}",
        f"- compiler_backend_type: {metrics.get('compiler_backend_type')}",
        "",
        "The v0.9.3 arithmetic positive signal is not maintained as verified sample-level improvement because the main gain is explainable by a deterministic index-period rule and aggregate records lack per-sample metric provenance.",
        "",
        "Still not proven: solved arithmetic, stable convergence, solved OOD, general program synthesis, same-size LLM advantage, safe real promotion, production readiness, real compiler-backed arithmetic.",
    ]
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_report(out: Path, readiness: Dict[str, Any], provenance: Dict[str, Any], leakage: Dict[str, Any], baseline: Dict[str, Any], rerun: Dict[str, Any]) -> None:
    lines = [
        "# v0.9.3.1 Arithmetic Signal Audit Report",
        "",
        "This audit checks whether v0.9.3's arithmetic_probe_positive_signal is real sample-level improvement.",
        "",
        f"- metric_provenance_passed: {readiness['metric_provenance_passed']}",
        f"- leakage_audit_passed: {readiness['leakage_audit_passed']}",
        f"- heldout_group_audit_passed: {readiness['heldout_group_audit_passed']}",
        f"- baseline_gap_verified: {readiness['baseline_gap_verified']}",
        f"- targeted_rerun_completed: {readiness['targeted_rerun_completed']}",
        f"- recommended_claim_level: {readiness['recommended_claim_level']}",
        "",
        "The audit does not claim solved arithmetic.",
    ]
    (out / "arithmetic_signal_audit_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
