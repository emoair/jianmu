from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class RuntimeCachePolicy:
    prefer_project_local_cache: bool = True
    user_allows_project_local_cache: bool = True
    avoid_onedrive_only_if_sync_active: bool = True
    fallback_external_cache: Optional[str] = None
    cleanup_runtime_cache: bool = False


def resolve_runtime_cache(project_dir: Path, runtime_cache_dir: Optional[str] = None, policy: RuntimeCachePolicy = None) -> Dict:
    policy = policy or RuntimeCachePolicy()
    if runtime_cache_dir:
        base = Path(runtime_cache_dir)
    elif policy.prefer_project_local_cache and policy.user_allows_project_local_cache:
        base = project_dir / ".jianmu_runtime_cache"
    elif policy.fallback_external_cache:
        base = Path(policy.fallback_external_cache)
    else:
        base = project_dir / ".jianmu_runtime_cache"
    run_dir = base / f"run_{uuid.uuid4().hex[:12]}"
    run_dir.mkdir(parents=True, exist_ok=True)
    test_path = run_dir / "write_test.tmp"
    test_path.write_text("ok", encoding="utf-8")
    project_inside_onedrive = "onedrive" in str(project_dir).lower()
    warning = ""
    if project_inside_onedrive and policy.user_allows_project_local_cache:
        warning = "project path contains OneDrive; user_allows_project_local_cache=true; onedrive_sync_state not_measured"
    try:
        free_mb = int(shutil.disk_usage(run_dir).free / (1024 * 1024))
    except Exception:
        free_mb = None
    return {
        "runtime_cache_dir": str(run_dir),
        "project_inside_onedrive": project_inside_onedrive,
        "user_allows_project_local_cache": policy.user_allows_project_local_cache,
        "onedrive_sync_state": "not_measured",
        "cache_policy_warning": warning,
        "cache_write_test_passed": test_path.read_text(encoding="utf-8") == "ok",
        "cache_free_space_mb": free_mb,
        "cleanup_performed": False,
    }

