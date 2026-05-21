from jianmu.self_learning.darwinforge.freebeam_boundary_eval import FreeBeamConfig, run_freebeam_boundary_eval


def test_freebeam_boundary_eval_does_not_use_labels_for_decision():
    samples = [
        {"sample_id": "s1", "raw_text": "x", "input_mode": "hard_ood", "boundary_label": "current_supported"},
        {"sample_id": "s2", "raw_text": "y", "input_mode": "zh_natural", "boundary_label": "hard_ood"},
    ]
    result = run_freebeam_boundary_eval(samples, {"available": True}, FreeBeamConfig())
    assert result["labels_used_for_decision"] is False
    assert result["decisions"][0]["freebeam_decision"] == "reject"
    assert result["decisions"][1]["freebeam_decision"] == "accept_as_supported"
    assert all(row["field"] != "boundary_label" for row in result["feature_access"])


def test_real_promotion_disabled():
    result = run_freebeam_boundary_eval([], {"available": True}, FreeBeamConfig())
    assert result["real_promotion_enabled"] is False


def test_free_eval_does_not_read_target_branch_path():
    result = run_freebeam_boundary_eval(
        [{"sample_id": "s1", "raw_text": "x", "input_mode": "hard_ood", "target_branch_path": ["forbidden"]}],
        {"available": True},
        FreeBeamConfig(),
    )
    assert all(row["field"] != "target_branch_path" for row in result["feature_access"])


def test_no_external_api_calls():
    import pathlib

    root = pathlib.Path("jianmu/self_learning/darwinforge")
    text = "\n".join((root / name).read_text(encoding="utf-8") for name in [
        "freebeam_boundary_eval.py",
        "no_label_inference_guard.py",
        "boundary_generalization_metrics.py",
        "freebeam_rejection_diagnostics.py",
        "heldout_boundary_slices.py",
    ])
    assert "requests" not in text
    assert "httpx" not in text
    assert "openai" not in text


def test_no_expression_oracle_import():
    import pathlib

    text = (pathlib.Path("jianmu/self_learning/darwinforge") / "freebeam_boundary_eval.py").read_text(encoding="utf-8")
    assert "expression_oracle" not in text
