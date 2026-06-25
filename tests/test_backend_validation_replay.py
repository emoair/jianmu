from jianmu.self_learning.darwinforge.backend_compiler_manifest import validate_backend_manifest_record


def test_backend_validation_replay_requires_real_subprocess() -> None:
    assert not validate_backend_manifest_record({"sample_id": "missing-pids"})

