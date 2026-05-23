from jianmu.self_learning.darwinforge.real_workload_audit import audit_v0_9_1_records


def test_real_mini_run_outputs_sample_counters(tmp_path):
    source = tmp_path / "v0_9_1"
    source.mkdir()
    (source / "large_scale_fullstate_metrics.json").write_text('{"mode":"xlarge","train_sample_count":50000,"eval_sample_count":12000,"external_ood_sample_count":15000,"recommended_claim_level":"large_completed_strong_signal"}\n', encoding="utf-8")
    (source / "runtime_profile.json").write_text('{"runtime_seconds_total":0.131871}\n', encoding="utf-8")
    (source / "fullstate_scale_profile.json").write_text("{}\n", encoding="utf-8")
    (source / "baseline_harness_summary.json").write_text('{"results":[]}\n', encoding="utf-8")
    (source / "ablation_harness_summary.json").write_text('{"results":[]}\n', encoding="utf-8")
    result = audit_v0_9_1_records(source, tmp_path / "out", "datasets", real_mini_train=2, real_mini_eval=1, real_mini_external_ood=1)
    assert result["real_mini"]["counters"]["actual_train_iterated_count"] == 2
    assert result["readiness"]["recommended_claim_level"] == "needs_real_longrun"
