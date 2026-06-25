from jianmu.self_learning.darwinforge.backend_compiler_manifest import build_backend_manifest_contract, validate_backend_manifest_record


def _row():
    return {"compile_invocation_id": "1", "sample_id": "s", "cycle_id": "c", "source_sha256": "x", "c_source_path": "a", "obj_path": "b", "exe_path": "c", "cl_command": [], "cl_pid": 1, "cl_start_monotonic": 1.0, "cl_end_monotonic": 2.0, "cl_returncode": 0, "link_command": [], "link_pid": 2, "link_start_monotonic": 2.0, "link_end_monotonic": 3.0, "link_returncode": 0, "exe_pid": 3, "exe_start_monotonic": 3.0, "exe_end_monotonic": 4.0, "exe_returncode": 0, "expected_stdout": "1", "actual_stdout": "1", "stdout_match": True, "cached": False, "stubbed": False}


def test_backend_compiler_manifest_requires_cl_pid(tmp_path) -> None:
    row = _row()
    assert validate_backend_manifest_record(row)
    del row["cl_pid"]
    assert not validate_backend_manifest_record(row)


def test_backend_compiler_manifest_requires_link_pid(tmp_path) -> None:
    row = _row()
    del row["link_pid"]
    assert not validate_backend_manifest_record(row)


def test_backend_compiler_manifest_requires_exe_pid(tmp_path) -> None:
    result = build_backend_manifest_contract(tmp_path, _row())
    assert result["exe_pid_recorded"] is True
    assert result["backend_manifest_contract_passed"] is True

