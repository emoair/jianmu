from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


def classify_process(name: str, cmdline: str = "") -> str:
    text = f"{name} {cmdline}".lower()
    if "python" in text and "jianmu" in text:
        return "jianmu_runner"
    if "python" in text:
        return "python_child"
    if "cl.exe" in text or text.strip() == "cl":
        return "msvc_cl"
    if "link.exe" in text or text.strip() == "link":
        return "msvc_link"
    if "program.exe" in text or "backend_" in text and ".exe" in text:
        return "generated_exe"
    if "git.exe" in text or " git " in text or "sh.exe" in text or "bash.exe" in text or "scalar.exe" in text:
        if any(marker in text for marker in ("core.hookspath=nul", "diff.mnemonicprefix", "status --porcelain", "ls-files", "write-tree", "add -a")):
            return "ide"
        return "git"
    if "onedrive.exe" in text:
        return "onedrive"
    if "msmpeng.exe" in text or "defender" in text or "antimalware" in text:
        return "defender"
    if "360" in text or "qh" in text and "safe" in text:
        return "antivirus_360"
    if "searchindexer" in text or "searchprotocolhost" in text:
        return "system"
    if "memory compression" in text:
        return "memory_compression"
    if any(name.lower().startswith(prefix) for prefix in ("system", "registry", "idle", "csrss", "wininit", "services", "lsass", "svchost")):
        return "system"
    return "unknown"


def classify_process_rows(rows: Iterable[dict]) -> dict:
    counts: dict[str, int] = {}
    suspected: set[str] = set()
    for row in rows:
        cls = classify_process(str(row.get("name", "")), str(row.get("cmdline", row.get("command_line", ""))))
        row["classification"] = cls
        counts[cls] = counts.get(cls, 0) + 1
        if cls in {"onedrive", "defender", "antivirus_360", "git", "ide", "system"}:
            suspected.add(cls)
    result = {
        "classifier_completed": True,
        "onedrive_activity_detected": counts.get("onedrive", 0) > 0,
        "defender_activity_detected": counts.get("defender", 0) > 0,
        "antivirus_360_activity_detected": counts.get("antivirus_360", 0) > 0,
        "git_activity_detected": counts.get("git", 0) > 0,
        "ide_git_activity_detected": counts.get("ide", 0) > 0,
        "windows_indexer_activity_detected": counts.get("system", 0) > 0,
        "suspected_external_memory_pressure_sources": sorted(suspected),
        "classification_counts": counts,
    }
    result["classifier_passed"] = True
    return result


def write_security_onedrive_git_classification(output_records: str | Path, rows: Iterable[dict]) -> dict:
    result = classify_process_rows(rows)
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "security_onedrive_git_classification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
