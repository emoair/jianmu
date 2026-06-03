def summarize_full_compile_50k_failures(continuation: dict) -> dict:
    return {
        "wrong_stdout_count": continuation.get("wrong_stdout_count_total", 0),
        "timeout_count": continuation.get("timeout_count_total", 0),
        "permission_error_count": continuation.get("permission_error_count_total", 0),
        "cleanup_failure_count": continuation.get("cleanup_failure_count_total", 0),
        "requires_followup": not continuation.get("full_compile_50k_clean", False),
    }


__all__ = ["summarize_full_compile_50k_failures"]
