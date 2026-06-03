def summarize_frontier_review_failures(blocking_issues: list[str]) -> dict[str, object]:
    return {
        "blocking_issue_count": len(blocking_issues),
        "blocking_issues": list(blocking_issues),
        "requires_human_review": True,
    }


__all__ = ["summarize_frontier_review_failures"]
