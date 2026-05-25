from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable


FAILURE_CATEGORIES = [
    "compile_syntax_error",
    "compile_toolchain_error",
    "compile_type_error",
    "runtime_error",
    "runtime_timeout",
    "wrong_output",
    "unsafe_expression_blocked",
    "overflow_or_semantic_risk",
    "trace_or_recording_error",
    "unknown",
]

ENGINEERING_FAILURE_CATEGORIES = {
    "compile_toolchain_error",
    "runtime_timeout",
    "trace_or_recording_error",
}

CANDIDATE_FAILURE_CATEGORIES = {
    "compile_syntax_error",
    "compile_type_error",
    "wrong_output",
    "unsafe_expression_blocked",
    "overflow_or_semantic_risk",
    "runtime_error",
}


def classify_compiler_failure(trace_row: Dict[str, Any], replay_result: Dict[str, Any] | None = None) -> str:
    result = replay_result or trace_row
    if not trace_row or not trace_row.get("sample_id_hash"):
        return "trace_or_recording_error"
    if result.get("missing_dataset_row") or result.get("trace_missing_expression"):
        return "trace_or_recording_error"
    if result.get("unsafe_expression"):
        return "unsafe_expression_blocked"
    if result.get("timeout"):
        if result.get("runtime_invoked") or result.get("notes") == "runtime_timeout":
            return "runtime_timeout"
        return "compile_toolchain_error"

    compile_returncode = result.get("compile_returncode")
    if compile_returncode not in (None, 0):
        stderr = str(result.get("compile_stderr_tail") or result.get("compile_stdout_tail") or result.get("notes") or "")
        return _classify_compile_error(stderr)

    runtime_returncode = result.get("runtime_returncode")
    if result.get("runtime_invoked") and runtime_returncode not in (None, 0):
        return "runtime_error"

    if result.get("compiler_verified_correct") is False:
        expression = str(result.get("expression_preview_if_safe") or "")
        if _has_semantic_risk(expression, str(result.get("notes") or "")):
            return "overflow_or_semantic_risk"
        return "wrong_output"

    return "unknown"


def summarize_failure_taxonomy(failures: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(failures)
    category_counts = Counter(row.get("failure_category", "unknown") for row in rows)
    stage_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        stage_counts[str(row.get("stage") or "unknown")][row.get("failure_category", "unknown")] += 1

    dominant = "none"
    if category_counts:
        dominant = category_counts.most_common(1)[0][0]
    engineering_count = sum(category_counts.get(name, 0) for name in ENGINEERING_FAILURE_CATEGORIES)
    candidate_count = sum(category_counts.get(name, 0) for name in CANDIDATE_FAILURE_CATEGORIES)
    total = sum(category_counts.values())
    return {
        "classified_failure_count": total,
        "unknown_failure_count": category_counts.get("unknown", 0),
        "failure_category_distribution": dict(sorted(category_counts.items())),
        "failure_stage_distribution": {
            stage: dict(sorted(counts.items())) for stage, counts in sorted(stage_counts.items())
        },
        "dominant_failure_category": dominant,
        "engineering_failure_count": engineering_count,
        "candidate_failure_count": candidate_count,
        "engineering_issue_dominant": engineering_count > candidate_count and engineering_count > 0,
        "candidate_error_dominant": candidate_count > engineering_count and candidate_count > 0,
    }


def _classify_compile_error(stderr: str) -> str:
    text = stderr.lower()
    if not text:
        return "unknown"
    toolchain_markers = [
        "cannot open",
        "permission denied",
        "not recognized",
        "no such file",
        "fatal error lnk",
        "lnk",
        "temporary",
        "timed out",
        "access is denied",
    ]
    if any(marker in text for marker in toolchain_markers):
        return "compile_toolchain_error"
    type_markers = ["overflow", "constant", "conversion", "truncation", "c4307", "c4146"]
    if any(marker in text for marker in type_markers):
        return "compile_type_error"
    syntax_markers = ["syntax error", "c2059", "c2143", "missing", "illegal token", "unexpected"]
    if any(marker in text for marker in syntax_markers):
        return "compile_syntax_error"
    return "compile_syntax_error"


def _has_semantic_risk(expression: str, notes: str) -> bool:
    text = f"{expression} {notes}".lower()
    if "overflow" in text or "semantic" in text:
        return True
    return "/" in expression and "-" in expression
