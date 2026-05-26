from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.bounded_substrate_full_readiness import assess_bounded_substrate_full_readiness
from jianmu.self_learning.darwinforge.bounded_substrate_full_rerun import _convert_metrics
from jianmu.self_learning.darwinforge.bounded_substrate_metric_provenance import audit_bounded_substrate_metric_provenance
from jianmu.self_learning.darwinforge.bounded_substrate_signal_audit import run_bounded_substrate_signal_audit
from jianmu.self_learning.darwinforge.bounded_substrate_worker_scaling import REQUIRED_WORKER_LEVELS, run_bounded_substrate_worker_scaling


def test_bounded_substrate_signal_audit_detects_metric_provenance(tmp_path: Path) -> None:
    src = _write_source_records(tmp_path / "src")
    out = tmp_path / "out"
    result = audit_bounded_substrate_metric_provenance(src, out)
    assert result["metric_provenance_passed"] is True
    assert (out / "metric_provenance.json").exists()


def test_bounded_substrate_signal_audit_blocks_fixed_summary(tmp_path: Path) -> None:
    src = _write_source_records(tmp_path / "src")
    rows = _trace_rows()
    rows[0]["used_fixed_metric"] = True
    _write_jsonl(src / "freebeam_after_trace.jsonl", rows)
    result = audit_bounded_substrate_metric_provenance(src, tmp_path / "out")
    assert result["fixed_value_detected"] is True
    assert result["metric_provenance_passed"] is False


def test_bounded_substrate_signal_audit_blocks_periodic_rule(tmp_path: Path) -> None:
    src = _write_source_records(tmp_path / "src")
    rows = _trace_rows()
    rows[0]["used_periodic_rule"] = True
    _write_jsonl(src / "freebeam_before_trace.jsonl", rows)
    result = audit_bounded_substrate_metric_provenance(src, tmp_path / "out")
    assert result["periodic_rule_detected"] is True


def test_bounded_substrate_signal_audit_checks_leakage(tmp_path: Path) -> None:
    src = _write_source_records(tmp_path / "src")
    dataset = _write_dataset_audits(tmp_path / "dataset")
    result = run_bounded_substrate_signal_audit(src, dataset, tmp_path / "out")
    assert result["signal_audit_completed"] is True
    assert result["heldout_train_input_leakage_count"] == 0


def test_bounded_substrate_full_rerun_uses_large_dataset() -> None:
    result = _convert_metrics({"modes_completed": ["full-probe"], "dataset_scales_used": ["large"], "train_count": 10}, ["full-probe"])
    assert result["dataset_scale_used"] == "large"


def test_bounded_substrate_full_rerun_marks_partial_correctly() -> None:
    result = _convert_metrics({"modes_completed": ["full-probe"], "train_count": 10}, ["full-probe"])
    assert result["modes_partial"]


def test_bounded_substrate_worker_scaling_levels() -> None:
    assert REQUIRED_WORKER_LEVELS == [8, 16, 32, 64]


def test_bounded_substrate_worker_scaling_uses_real_cl(monkeypatch, tmp_path: Path) -> None:
    def fake_validation(*args, **kwargs):
        out = Path(args[1])
        out.mkdir(parents=True, exist_ok=True)
        return {
            "backend_type": "real_c_compiler",
            "compiler_name": "cl",
            "real_compiler_invocation_count": 2,
            "compile_success_count": 2,
            "runtime_success_count": 2,
            "compiler_verified_correct_rate": 1.0,
            "boundary_compiler_misroute_count": 0,
            "timeout_count": 0,
            "compile_failure_count": 0,
            "runtime_failure_count": 0,
            "p50_latency_ms": 1.0,
            "p95_latency_ms": 1.0,
            "p99_latency_ms": 1.0,
            "samples_per_second": float(args[3]),
        }

    monkeypatch.setattr("jianmu.self_learning.darwinforge.bounded_substrate_worker_scaling.run_bounded_substrate_compiler_validation", fake_validation)
    result = run_bounded_substrate_worker_scaling("dataset", tmp_path, [8, 16], supported_samples=1, boundary_samples=1)
    assert result["best_worker_count_for_bounded_substrate"] == 16
    assert result["stable_worker_levels"] == [8, 16]


def test_bounded_substrate_full_readiness_no_turing_complete_claim(tmp_path: Path) -> None:
    _write_json(tmp_path / "compiler_validation_metrics.json", {"backend_type": "real_c_compiler", "compiler_name": "cl", "compile_worker_count": 16, "real_compiler_invocation_count": 1, "compiler_verified_correct_rate": 1.0, "boundary_compiler_misroute_count": 0})
    result = assess_bounded_substrate_full_readiness(
        tmp_path,
        {"signal_audit_passed": True},
        {"supported_candidate_hit_before": 0.1, "supported_candidate_hit_after": 0.2, "top1_supported_correct_before": 0.1, "top1_supported_correct_after": 0.2, "baseline_gap_verified": True},
        {"worker_scaling_completed": True, "best_worker_count_for_bounded_substrate": 16, "recommended_default_worker_count": 16},
    )
    assert "turing_complete" not in str(result).lower()
    assert result["recommended_claim_level"] == "bounded_substrate_full_positive_signal_verified"


def test_no_expression_oracle_import() -> None:
    text = _bounded_text()
    assert "expression_oracle" not in text


def test_no_external_api_calls() -> None:
    text = _bounded_text().lower()
    assert "openai" not in text
    assert "requests." not in text


def test_no_hardcoded_keyword_gate() -> None:
    assert "keyword gate" not in _bounded_text().lower()


def test_real_promotion_disabled() -> None:
    from jianmu.self_learning.darwinforge.turing_substrate_curriculum_schedule import build_turing_substrate_curriculum_schedule

    assert all(not row["real_promotion_allowed"] for row in build_turing_substrate_curriculum_schedule()["stages"])


def _write_source_records(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _write_json(path / "bounded_substrate_training_metrics.json", {
        "supported_candidate_hit_before": 0.5,
        "supported_candidate_hit_after": 0.5,
        "correct_output_in_beam_before": 0.5,
        "correct_output_in_beam_after": 0.5,
        "top1_supported_correct_before": 0.5,
        "top1_supported_correct_after": 0.5,
        "forbidden_field_access_count": 0,
        "expected_output_access_before_candidate_generation": False,
        "target_ir_access_before_candidate_generation": False,
    })
    _write_jsonl(path / "freebeam_before_trace.jsonl", _trace_rows())
    _write_jsonl(path / "freebeam_after_trace.jsonl", _trace_rows())
    _write_jsonl(path / "heldout_freebeam_trace.jsonl", [{**_trace_rows()[0], "sample_id_hash": "heldout-only"}])
    _write_json(path / "compiler_validation_metrics.json", {"backend_type": "real_c_compiler", "compiler_name": "cl"})
    _write_json(path / "bounded_substrate_baseline_ablation.json", {"baseline_gap_verified": True, "variants": {"full_jianmu_bounded_substrate": {"fixed_summary_detected": False}, "random_router": {"fixed_summary_detected": False}, "heuristic_router": {"fixed_summary_detected": False}, "no_root_colony": {"fixed_summary_detected": False}, "no_nutrient_toxic_memory": {"fixed_summary_detected": False}}})
    (path / "failure_analysis.md").write_text("# Failure Analysis\n", encoding="utf-8")
    (path / "failure_examples.jsonl").write_text("", encoding="utf-8")
    return path


def _trace_rows() -> list[dict]:
    return [
        {"sample_id_hash": "a", "stage": "variable_declaration", "category": "current_supported_turing_substrate", "candidate_hit": True, "correct_output_in_beam": True, "top1_correct": True, "used_fixed_metric": False, "used_periodic_rule": False, "used_summary_metric": False},
        {"sample_id_hash": "b", "stage": "assignment_sequence", "category": "current_supported_turing_substrate", "candidate_hit": False, "correct_output_in_beam": False, "top1_correct": False, "used_fixed_metric": False, "used_periodic_rule": False, "used_summary_metric": False},
    ]


def _write_dataset_audits(path: Path) -> Path:
    for scale in ["small", "medium", "large"]:
        (path / scale).mkdir(parents=True, exist_ok=True)
        _write_json(path / scale / "audit.json", {"audit_passed": True, "blocking_issue_count": 0})
    return path


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _bounded_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in Path("jianmu/self_learning/darwinforge").glob("bounded_substrate_*.py"))
