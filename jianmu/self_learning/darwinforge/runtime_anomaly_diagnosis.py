from __future__ import annotations

from typing import Any, Dict


def diagnose_runtime_anomaly(runtime_profile: Dict[str, Any], scale_profile: Dict[str, Any], counters: Dict[str, Any], workload_summary: Dict[str, Any], pytest_runtime_seconds: float | None = None) -> Dict[str, Any]:
    records_runtime = float(runtime_profile.get("runtime_seconds_total", runtime_profile.get("runtime_seconds", 0.0)) or 0.0)
    reported_total = (
        int(counters.get("reported_train_count", 0))
        + int(counters.get("reported_eval_count", 0))
        + int(counters.get("reported_external_ood_count", 0))
    )
    actual_total = (
        int(counters.get("actual_train_iterated_count", 0))
        + int(counters.get("actual_eval_iterated_count", 0))
        + int(counters.get("actual_external_ood_iterated_count", 0))
    )
    unrealistic = reported_total >= 10_000 and records_runtime < 10.0 and actual_total == 0
    severity = "blocking" if unrealistic else "medium" if counters.get("synthetic_summary_detected") else "none"
    return {
        "runtime_anomaly_detected": severity != "none",
        "anomaly_severity": severity,
        "likely_cause": "v0.9.1 runner generated fixed metric summaries / harness probe records without real per-sample iteration counters" if unrealistic else "none",
        "records_total_runtime_seconds": records_runtime,
        "pytest_runtime_seconds": pytest_runtime_seconds,
        "reported_total_sample_count": reported_total,
        "actual_total_iterated_count": actual_total,
        "runtime_includes_pytest": False,
        "runtime_includes_real_sample_iteration": actual_total > 0,
        "runtime_includes_cross_process_subprocess": False,
        "runtime_includes_baseline_ablation": False,
        "xlarge_runtime_plausible": not unrealistic,
        "real_workload_completed": actual_total > 0 and counters.get("count_match_passed", False),
        "harness_probe_completed": True,
        "longrun_required": True,
        "recommended_next_action": "run v0.9.1.2 real longrun with mandatory per-sample counters and subprocess traces" if severity == "blocking" else "continue validation",
    }


def write_runtime_anomaly_report_md(report: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Runtime Anomaly Diagnosis",
            "",
            f"- runtime_anomaly_detected: {report['runtime_anomaly_detected']}",
            f"- anomaly_severity: {report['anomaly_severity']}",
            f"- likely_cause: {report['likely_cause']}",
            f"- records_total_runtime_seconds: {report['records_total_runtime_seconds']}",
            f"- reported_total_sample_count: {report['reported_total_sample_count']}",
            f"- actual_total_iterated_count: {report['actual_total_iterated_count']}",
            f"- xlarge_runtime_plausible: {report['xlarge_runtime_plausible']}",
            f"- recommended_next_action: {report['recommended_next_action']}",
        ]
    ) + "\n"
