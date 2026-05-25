import json
from pathlib import Path

from jianmu.self_learning.darwinforge.arithmetic_signal_audit import run_arithmetic_signal_audit


def _row(i, split, stage="precedence", category="current_supported_arithmetic"):
    supported = category == "current_supported_arithmetic"
    return {
        "id": f"{split}-{stage}-{i}",
        "split": split,
        "category": category,
        "stage": stage,
        "input": f"{i}+1",
        "expected_output": f"{i + 1}\n" if supported else None,
        "expression_group_id": f"eg-{split}-{stage}-{i}",
        "paraphrase_group_id": f"pg-{split}-{stage}-{i}",
        "target_group_id": f"tg-{split}-{stage}-{i}" if supported else None,
    }


def _records(root: Path):
    root.mkdir()
    (root / "arithmetic_training_metrics.json").write_text(json.dumps({
        "recommended_claim_level": "arithmetic_probe_positive_signal",
        "compiler_backend_type": "internal_evaluator",
        "forbidden_field_access_count": 0,
        "supported_candidate_hit_before": 0.8,
        "supported_candidate_hit_after": 0.95,
        "actual_eval_iterated_count": 10,
        "actual_heldout_iterated_count": 10,
        "unsupported_false_accept_rate": 0.0,
        "trap_false_accept_rate": 0.0,
        "future_domain_supported_accept_rate": 0.0,
        "near_ood_supported_accept_rate": 0.0,
    }), encoding="utf-8")
    (root / "arithmetic_stage_metrics.json").write_text(json.dumps({"stages": []}), encoding="utf-8")


def _dataset(root: Path):
    for split in ["train", "eval", "test", "heldout"]:
        path = root / "small" / split
        path.mkdir(parents=True, exist_ok=True)
        rows = [_row(i, split, ["precedence", "parentheses", "negative_numbers", "exact_division"][i % 4]) for i in range(80)]
        rows += [_row(100 + i, split, "boundary", "hard_ood") for i in range(20)]
        (path / f"{split}_000.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_signal_audit_downgrades_fixed_summary_signal(tmp_path):
    records = tmp_path / "records"
    dataset = tmp_path / "dataset"
    _records(records)
    _dataset(dataset)
    result = run_arithmetic_signal_audit(records, dataset, tmp_path / "out", heldout_samples=40, boundary_samples=20)
    readiness = result["readiness"]
    assert readiness["recommended_claim_level"] == "signal_not_verified"
    assert readiness["fixed_value_detected"] is True
    assert readiness["v0_9_3_claim_after"] == "arithmetic_probe_mixed_signal_needs_per_sample_rerun"
