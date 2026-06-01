from jianmu.self_learning.darwinforge.rc1_preparation_bundle import generate_rc1_preparation_bundle


def test_rc1_preparation_bundle_generated(tmp_path):
    result = generate_rc1_preparation_bundle(tmp_path)
    assert result["rc1_preparation_bundle_generated"] is True
    assert result["ready_for_v1_0_rc1_branch"] is True
    assert result["ready_for_v1_0_release"] is False
