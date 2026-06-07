from jianmu.self_learning.darwinforge.extended_ir_path_tracer import trace_policy_path


def test_extended_ir_path_tracer_records_policy_builder_ir_emitter():
    row = trace_policy_path("canonical_function_targetir", 7)
    assert row["target_builder_policy"] == "canonical_function_targetir"
    assert row["builder"] == "function_builder"
    assert row["extended_ir"] is True
    assert row["emitter"] == "ExtendedEmitterC"
    assert row["c_source_generated"] is True

