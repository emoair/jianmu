from jianmu.self_learning.darwinforge.layerwise_compiler_failure_analysis import write_layerwise_compiler_integrity


def test_integrity_original_result_preserved(tmp_path):
    integrity = write_layerwise_compiler_integrity(tmp_path)
    assert integrity["original_v0_9_12_2_result_preserved"] is True
    assert integrity["no_cached_compiler_result_used_as_validation"] is True
