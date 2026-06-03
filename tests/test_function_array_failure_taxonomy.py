from jianmu.self_learning.darwinforge.function_array_failure_taxonomy import ARRAY_FAILURES, FUNCTION_FAILURES, run_failure_taxonomy


def test_function_array_failure_taxonomy(tmp_path):
    result = run_failure_taxonomy(tmp_path)
    for item in FUNCTION_FAILURES:
        assert item in result["function_failure_distribution"]
    for item in ARRAY_FAILURES:
        assert item in result["array_failure_distribution"]
    assert result["taxonomy_completed"] is True
