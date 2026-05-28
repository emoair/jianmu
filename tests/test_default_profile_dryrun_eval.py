from jianmu.self_learning.darwinforge.default_profile_dryrun_eval import run_default_profile_dryrun_eval


def test_default_dryrun_eval_compares_profiles(tmp_path):
    d = tmp_path / "large" / "train"
    d.mkdir(parents=True)
    (d / "s.jsonl").write_text('{"id":"a","category":"current_supported_bounded_substrate","split":"train"}\n', encoding="utf-8")
    result = run_default_profile_dryrun_eval(tmp_path, tmp_path / "out", ["actual_current_default_reference", "layerwise_sparse_1B_freeze_prune_dryrun_default"], 1, 0, [92])
    assert len(result["profiles"]) == 2
    assert any(row["is_dry_run_default"] for row in result["profiles"])
