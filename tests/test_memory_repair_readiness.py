from jianmu.self_learning.darwinforge.memory_repair_readiness import build_memory_repair_readiness


def test_memory_repair_readiness_keeps_production_false(tmp_path) -> None:
    payload = {
        "memory_pressure_audit_completed": True,
        "memory_snapshot_contract_passed": True,
        "streaming_dataset_writer_passed": True,
        "streaming_manifest_writer_passed": True,
        "bounded_queue_backpressure_passed": True,
        "subprocess_output_streaming_passed": True,
        "cycle_cleanup_barrier_passed": True,
        "memory_pressure_checkpoint_passed": True,
        "memory_stress_validation_passed": True,
        "trace_shard_size_cap_passed": True,
        "git_cleanup_guard_passed": True,
        "lifecycle_guard_passed": True,
    }
    result = build_memory_repair_readiness(tmp_path, payload)
    assert result["recommended_claim_level"] == "memory_lifecycle_streaming_repair_positive"
    assert result["production_function_support_completed"] is False
