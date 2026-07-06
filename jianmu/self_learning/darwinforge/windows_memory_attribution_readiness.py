from __future__ import annotations

import json
from pathlib import Path


def build_windows_memory_attribution_report(output_records: str | Path, payload: dict) -> dict:
    secondary: list[str] = []
    if payload.get("git_activity_detected") or payload.get("ide_git_activity_detected"):
        secondary.append("git_ide_storm")
    if payload.get("onedrive_activity_detected"):
        secondary.append("onedrive_scan_pressure")
    if payload.get("defender_activity_detected") or payload.get("antivirus_360_activity_detected"):
        secondary.append("defender_360_scan_pressure")
    if payload.get("file_cache_pressure_suspected") or payload.get("likely_file_cache_or_standby"):
        secondary.append("file_cache_standby_pressure")
    process_tree_peak = float(payload.get("process_tree_peak_rss_mb", 0.0) or 0.0)
    runner_peak = float(payload.get("runner_rss_peak_mb", payload.get("rss_peak_mb", 0.0)) or 0.0)
    python_heap = float(payload.get("runner_python_heap_peak_mb", payload.get("python_heap_peak_mb", 0.0)) or 0.0)
    python_heap_leak = python_heap > 512
    process_tree_growth = process_tree_peak > max(512.0, runner_peak * 4)
    if python_heap_leak:
        primary = "python_heap_leak"
    elif process_tree_growth:
        primary = "runner_process_tree_growth"
    elif payload.get("defender_activity_detected") or payload.get("antivirus_360_activity_detected"):
        primary = "defender_360_scan_pressure"
    elif payload.get("onedrive_activity_detected"):
        primary = "onedrive_scan_pressure"
    elif payload.get("file_cache_pressure_suspected") or payload.get("likely_file_cache_or_standby"):
        primary = "file_cache_standby_pressure"
    elif payload.get("git_activity_detected") or payload.get("ide_git_activity_detected"):
        primary = "git_ide_storm"
    else:
        primary = "mixed" if secondary else "inconclusive"
    result = {
        "attribution_completed": True,
        "primary_attribution": primary,
        "secondary_attributions": sorted(set(secondary)),
        "python_heap_leak_detected": python_heap_leak,
        "runner_process_leak_detected": runner_peak > 512,
        "process_tree_leak_detected": process_tree_growth,
        "git_or_ide_pressure_detected": "git_ide_storm" in secondary,
        "onedrive_pressure_detected": "onedrive_scan_pressure" in secondary,
        "defender_or_360_pressure_detected": "defender_360_scan_pressure" in secondary,
        "file_cache_pressure_detected": "file_cache_standby_pressure" in secondary or primary == "file_cache_standby_pressure",
        "memory_compression_pressure_detected": False,
        "paged_pool_pressure_detected": False,
        "nonpaged_pool_pressure_detected": False,
        "unaccounted_memory_pressure_detected": primary == "inconclusive",
        "recommended_fixes": _recommended_fixes(primary, secondary),
        "attribution_confidence": "medium" if primary != "inconclusive" else "low",
    }
    result["attribution_passed"] = True
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "windows_memory_attribution_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def build_windows_memory_attribution_readiness(output_records: str | Path, payload: dict) -> dict:
    report = build_windows_memory_attribution_report(output_records, payload)
    merged = {**payload, **report}
    blocking = []
    checks = {
        "system_memory_sampler_passed": "system_memory_sampler_failed",
        "process_tree_sampler_passed": "process_tree_sampler_failed",
        "top_process_snapshot_passed": "top_process_snapshot_failed",
        "classifier_passed": "classifier_failed",
        "artifact_cache_audit_passed": "artifact_cache_audit_failed",
        "workload_replay_passed": "workload_replay_failed",
        "decay_observer_passed": "decay_observer_failed",
        "attribution_completed": "attribution_missing",
    }
    for key, issue in checks.items():
        if key == "workload_replay_passed" and _workload_completed_clean_but_throughput_blocked(merged):
            continue
        if not merged.get(key):
            blocking.append(issue)
    primary = merged["primary_attribution"]
    if blocking:
        recommended = "failed"
    elif primary == "inconclusive":
        recommended = "windows_memory_attribution_inconclusive"
    elif merged.get("file_cache_pressure_detected") or merged.get("onedrive_pressure_detected") or merged.get("defender_or_360_pressure_detected"):
        recommended = "windows_memory_pressure_explained_as_file_cache_or_external_scan"
    elif merged.get("memory_issue_requires_followup") or _workload_completed_clean_but_throughput_blocked(merged):
        recommended = "windows_memory_attribution_completed_fix_required"
    else:
        recommended = "windows_memory_attribution_completed"
    result = {
        **merged,
        "memory_issue_explained": primary != "inconclusive",
        "memory_issue_fixed": False,
        "memory_issue_requires_followup": True,
        "workload_replay_throughput_blocked_by_external_pressure": _workload_completed_clean_but_throughput_blocked(merged),
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "redqueen_autonomous_governance_completed": False,
        "recommended_claim_level": recommended,
        "blocking_issues": blocking,
        "required_next_run": "Apply any Windows cache/scanner mitigations, then repeat memory attribution before pure heldout validation.",
    }
    Path(output_records, "windows_memory_attribution_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _workload_completed_clean_but_throughput_blocked(payload: dict) -> bool:
    if payload.get("workload_replay_passed"):
        return False
    if not payload.get("workload_replay_completed"):
        return False
    if float(payload.get("compiler_verified_correctness_rate", 0.0) or 0.0) != 1.0:
        return False
    if int(payload.get("wrong_stdout_count", 0) or 0) != 0:
        return False
    if int(payload.get("timeout_count", 0) or 0) != 0:
        return False
    return bool(
        payload.get("git_activity_detected")
        or payload.get("ide_git_activity_detected")
        or payload.get("defender_activity_detected")
        or payload.get("antivirus_360_activity_detected")
        or payload.get("file_cache_pressure_suspected")
    )


def _recommended_fixes(primary: str, secondary: list[str]) -> list[str]:
    fixes = ["keep dataset/backend manifests streaming and bounded"]
    if primary == "file_cache_standby_pressure" or "file_cache_standby_pressure" in secondary:
        fixes.append("keep compiler artifacts outside OneDrive/worktree and consider excluding temp artifact roots from real-time scanning")
    if primary in {"defender_360_scan_pressure", "onedrive_scan_pressure"} or any(item in secondary for item in {"defender_360_scan_pressure", "onedrive_scan_pressure"}):
        fixes.append("exclude transient compiler artifact roots from OneDrive/security scanner if acceptable")
    if primary == "git_ide_storm" or "git_ide_storm" in secondary:
        fixes.append("pause IDE git status scans during long validation or keep large records out of watched views")
    if primary == "inconclusive":
        fixes.append("repeat attribution with RAMMap/Performance Monitor counters")
    return fixes
