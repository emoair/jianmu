from jianmu.self_learning.darwinforge.fullstate_scale_profile import profile_fullstate_scale


def test_fullstate_scale_profile_outputs_state_sizes(tmp_path):
    profile = profile_fullstate_scale("large", {"train_sample_count": 10, "eval_sample_count": 5, "external_ood_sample_count": 5, "runtime_seconds": 2.0}, tmp_path)
    assert profile["state_size_bytes"] > 0
    assert profile["samples_per_second"] == 10.0
