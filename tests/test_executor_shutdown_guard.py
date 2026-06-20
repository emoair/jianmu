from jianmu.self_learning.darwinforge.executor_shutdown_guard import verify_executor_shutdown_guard


def test_executor_shutdown_guard_closes_thread_pools():
    result = verify_executor_shutdown_guard()
    assert result["thread_pool_shutdown_confirmed"] is True
    assert result["executor_shutdown_guard_passed"] is True


def test_executor_shutdown_guard_closes_process_pools():
    result = verify_executor_shutdown_guard()
    assert result["process_pool_shutdown_confirmed"] is True
    assert result["active_child_process_count_after_run"] == 0
