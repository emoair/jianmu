from jianmu.self_learning.darwinforge.batch_compile_clean_msvc_preflight import write_clean_msvc_preflight


def test_clean_msvc_preflight(tmp_path):
    result = write_clean_msvc_preflight(tmp_path)
    assert "preflight_passed" in result
    assert "cl_zs_test_passed" in result
    assert "temp_dir_writable" in result
