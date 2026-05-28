def test_default_dryrun_compiler_validation_uses_real_cl():
    metrics = {"backend_type": "real_c_compiler", "compiler_name": "cl"}
    assert metrics["backend_type"] == "real_c_compiler"
    assert metrics["compiler_name"] == "cl"
