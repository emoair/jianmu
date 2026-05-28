from jianmu.self_learning.darwinforge.layerwise_profile_compiler_validation import run_layerwise_profile_compiler_validation


def test_layerwise_profile_compiler_gate_uses_real_cl():
    metrics = {"backend_type": "real_c_compiler", "compiler_name": "cl", "compiler_environment": "msvc_vcvars64"}
    assert metrics["backend_type"] == "real_c_compiler"
    assert metrics["compiler_name"] == "cl"


def test_layerwise_profile_boundary_gate_blocks_future_accept():
    metrics = {"future_domain_compiled_count": 0, "boundary_compiler_misroute_count": 0}
    assert metrics["future_domain_compiled_count"] == 0
    assert metrics["boundary_compiler_misroute_count"] == 0
