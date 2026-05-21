from jianmu.self_learning.darwinforge.split_diagnostics import compute_split_diagnostics


def test_split_diagnostics_reports_limit_mismatch_reason():
    result = compute_split_diagnostics(
        "datasets/v0_7_0",
        {"train": 3000, "eval": 1000, "ood": 500},
        {"train": 2200, "eval": 600, "ood": 200},
    )
    assert result["reason_for_limit_mismatch"] == "dataset_capacity"
    assert result["split_hash_train"]
    assert result["dataset_capacity_train"] >= result["actual_train_count"]
