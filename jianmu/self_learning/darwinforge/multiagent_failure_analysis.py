from __future__ import annotations


def multiagent_failure_summary(blocking_issues: list[str]) -> dict[str, object]:
    return {"blocking_issues": blocking_issues, "failure_count": len(blocking_issues)}
