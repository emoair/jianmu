from jianmu.self_learning.darwinforge.longhaul_symbiote_runner import build_longhaul_data_mix_manifest


def test_longhaul_runner_checkpoint_resume(tmp_path):
    manifest = build_longhaul_data_mix_manifest(tmp_path)
    assert manifest["data_mix_passed"] is True
    assert manifest["trunk_solved_program_ratio_max"] <= 0.10
