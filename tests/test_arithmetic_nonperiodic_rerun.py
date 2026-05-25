from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.arithmetic_candidate_trace import aggregate_candidate_trace, trace_candidate_sample, train_nonperiodic_state
from jianmu.self_learning.darwinforge.arithmetic_nonperiodic_readiness import assess_nonperiodic_readiness
from jianmu.self_learning.darwinforge.arithmetic_nonperiodic_rerun import run_nonperiodic_arithmetic_rerun


def _row(idx: int, split: str, stage: str, expression: str, expected: str, operators: list[str]) -> dict:
    return {
        "id": f"{split}-{stage}-{idx}",
        "dataset_version": "v0.9.2",
        "split": split,
        "stage": stage,
        "category": "current_supported_arithmetic",
        "input": expression,
        "canonical_expression": expression,
        "target_ir": {"op": "int", "value": int(expected)},
        "expected_output": expected,
        "expected_type": "int",
        "boundary_label": "current_supported_arithmetic",
        "expected_action": "accept_supported",
        "nutrient_policy": {},
        "toxicity_policy": {},
        "operator_set": operators,
        "operator_count": len(operators),
        "integer_range": [-10, 10],
        "has_parentheses": "(" in expression,
        "has_unary_minus": expression.startswith("-") or "(-" in expression,
        "has_division": "/" in expression,
        "division_kind": "exact" if "/" in expression else "none",
        "expression_depth": 2,
        "result_abs": abs(int(expected)),
        "template_id": stage,
        "expression_group_id": f"group-{idx}",
        "paraphrase_group_id": f"para-{idx}",
        "target_group_id": f"target-{idx}",
        "leakage_guard": {},
        "provenance": {"generator": "test", "seed": 42, "generation_rule": stage},
    }


def _boundary(idx: int, split: str, category: str, text: str, stage: str = "boundary_rejection") -> dict:
    return {
        "id": f"{split}-{category}-{idx}",
        "dataset_version": "v0.9.2",
        "split": split,
        "stage": stage,
        "category": category,
        "input": text,
        "canonical_expression": None,
        "target_ir": None,
        "expected_output": None,
        "expected_type": "unsupported",
        "boundary_label": category,
        "expected_action": "reject",
        "nutrient_policy": {},
        "toxicity_policy": {},
        "operator_set": [],
        "operator_count": 0,
        "integer_range": [-10, 10],
        "has_parentheses": False,
        "has_unary_minus": False,
        "has_division": False,
        "division_kind": "none",
        "expression_depth": 0,
        "result_abs": None,
        "template_id": category,
        "expression_group_id": f"boundary-{idx}",
        "paraphrase_group_id": f"boundary-para-{idx}",
        "target_group_id": None,
        "leakage_guard": {},
        "provenance": {"generator": "test", "seed": 42, "generation_rule": category},
    }


def _write_dataset(root: Path) -> None:
    train_rows = [
        _row(1, "train", "single_op", "1+1", "2", ["+"]),
        _row(2, "train", "two_op_no_parentheses", "1+2+3", "6", ["+", "+"]),
        _row(3, "train", "precedence", "1+2*3", "7", ["+", "*"]),
        _row(4, "train", "parentheses", "(1+2)*3", "9", ["+", "*"]),
        _row(5, "train", "negative_numbers", "-3+5", "2", ["+"]),
        _row(6, "train", "exact_division", "8/2", "4", ["/"]),
        _row(7, "train", "precedence", "2+3*4", "14", ["+", "*"]),
        _row(8, "train", "parentheses", "(2+3)*4", "20", ["+", "*"]),
        _row(9, "train", "negative_numbers", "3*(-2)", "-6", ["*"]),
        _row(10, "train", "exact_division", "12/3", "4", ["/"]),
        _boundary(1, "train", "unsupported_arithmetic_boundary", "1 / 0"),
        _boundary(2, "train", "true_false_accept_trap", "3 + apple", "trap_rejection"),
    ]
    eval_rows = [
        _boundary(3, "eval", "future_domain_candidate", "3.14 * 2", "future_near_ood_quarantine"),
        _boundary(4, "eval", "near_ood_arithmetic", "7 / 2", "future_near_ood_quarantine"),
        _boundary(5, "eval", "hard_ood", "tell me a joke"),
    ]
    for scale in ["small", "medium"]:
        for split, rows in {"train": train_rows, "eval": eval_rows, "test": eval_rows, "heldout": eval_rows}.items():
            split_dir = root / scale / split
            split_dir.mkdir(parents=True, exist_ok=True)
            (split_dir / f"{split}_000.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )


def test_candidate_trace_has_per_sample_records() -> None:
    rows = [_row(1, "train", "precedence", "1+2*3", "7", ["+", "*"])]
    state = train_nonperiodic_state(rows)
    trace = trace_candidate_sample(rows[0], state, beam_size=8, phase="after")
    assert trace["sample_id_hash"]
    assert trace["candidate_count"] == 1
    assert trace["correct_output_in_beam"] is True
    assert trace["used_periodic_rule"] is False


def test_candidate_trace_does_not_include_expected_output_before_scoring() -> None:
    row = _row(1, "train", "single_op", "1+1", "2", ["+"])
    trace = trace_candidate_sample(row, train_nonperiodic_state([row]), phase="after")
    assert trace["expected_output_access_phase"] == "after_candidate_generation_for_scoring"
    assert trace["target_ir_access_phase"] == "none"


def test_nonperiodic_metrics_are_aggregated_from_samples(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    out = tmp_path / "records"
    _write_dataset(dataset)
    metrics = run_nonperiodic_arithmetic_rerun(dataset, tmp_path / "v0_9_3", out, ["quick"], [42], heldout_samples=6, boundary_samples=6)
    manifest = json.loads((out / "candidate_trace_manifest.json").read_text(encoding="utf-8"))
    trace_rows = []
    for shard in manifest["shards"]:
        trace_rows.extend(json.loads(line) for line in (out / shard).read_text(encoding="utf-8").splitlines())
    after_rows = [row for row in trace_rows if row["phase"] == "after" and row["method"] == "full_jianmu_nonperiodic"]
    recomputed = aggregate_candidate_trace(after_rows)
    assert metrics["supported_candidate_hit_after"] == recomputed["supported_candidate_hit_rate"]
    assert metrics["summary_only_detected"] is False


def test_nonperiodic_readiness_downgrades_fixed_summary() -> None:
    readiness = assess_nonperiodic_readiness({
        "nonperiodic_rerun_completed": True,
        "per_sample_trace_completed": True,
        "metric_provenance_passed": True,
        "leakage_guard_passed": True,
        "periodic_rule_detected": False,
        "fixed_value_detected": True,
        "summary_only_detected": True,
        "boundary_safety_preserved": True,
        "supported_candidate_hit_before": 0.4,
        "supported_candidate_hit_after": 0.8,
        "top1_before": 0.4,
        "top1_after": 0.8,
        "baseline_gap_verified": True,
        "internal_evaluator_only": True,
    })
    assert readiness["recommended_claim_level"] == "signal_not_verified"
    assert readiness["blocking_issues"]


def test_nonperiodic_rerun_blocks_index_period_rule() -> None:
    source = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in [
            "jianmu/self_learning/darwinforge/arithmetic_candidate_trace.py",
            "jianmu/self_learning/darwinforge/arithmetic_nonperiodic_rerun.py",
        ]
    )
    forbidden = ["sample_index %", "index %", "i % 20", "fixed 0.95", "success mask"]
    assert not any(pattern in source for pattern in forbidden)


def test_no_expression_oracle_import() -> None:
    source = Path("jianmu/self_learning/darwinforge/arithmetic_nonperiodic_rerun.py").read_text(encoding="utf-8")
    assert "expression_oracle" not in source


def test_no_external_api_calls() -> None:
    source = "\n".join(Path(path).read_text(encoding="utf-8") for path in [
        "jianmu/self_learning/darwinforge/arithmetic_candidate_trace.py",
        "jianmu/self_learning/darwinforge/arithmetic_nonperiodic_rerun.py",
    ])
    assert "openai" not in source.lower()
    assert "requests." not in source


def test_no_hardcoded_keyword_gate() -> None:
    source = Path("jianmu/self_learning/darwinforge/arithmetic_candidate_trace.py").read_text(encoding="utf-8")
    assert "keyword" not in source.lower()


def test_real_promotion_disabled() -> None:
    source = Path("jianmu/self_learning/darwinforge/arithmetic_nonperiodic_rerun.py").read_text(encoding="utf-8")
    assert "real_promotion" not in source
