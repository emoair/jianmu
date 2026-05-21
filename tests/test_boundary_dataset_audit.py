from jianmu.self_learning.datasets.boundary_aware_generator import generate_boundary_aware_samples
from jianmu.self_learning.datasets.boundary_dataset_audit import audit_boundary_dataset
from jianmu.self_learning.datasets.boundary_scale_builder import split_boundary_samples


def test_dataset_audit_detects_duplicate_inputs():
    row = generate_boundary_aware_samples(10, seed=1)[0]
    audit = audit_boundary_dataset({"train": [row, dict(row)], "eval_unseen_target": []})
    assert audit["duplicate_input_count"] == 1
    assert not audit["audit_passed"]


def test_dataset_audit_detects_train_eval_leakage():
    row = generate_boundary_aware_samples(10, seed=2)[0]
    audit = audit_boundary_dataset({"train": [row], "eval_unseen_target": [dict(row)]})
    assert audit["train_eval_input_leakage_count"] == 1


def test_dataset_audit_detects_non_supported_targetir_leak():
    row = next(r for r in generate_boundary_aware_samples(100, seed=3) if r["boundary_label"] != "current_supported")
    row = dict(row)
    row["target_ir"] = "lit(1)"
    audit = audit_boundary_dataset({"train": [row]})
    assert audit["non_supported_has_targetir_count"] == 1
