from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Dict, Optional


def default_runtime_cache_dir(project_dir: Optional[Path] = None) -> Path:
    d_root = Path("D:/")
    root = d_root if d_root.exists() else Path("C:/")
    return root / "jianmu-runtime-cache"


def init_runtime_cache(project_dir: Path, runtime_cache_dir: Optional[str] = None, cleanup_runtime_cache: bool = False) -> Dict:
    cache_dir = Path(runtime_cache_dir) if runtime_cache_dir else default_runtime_cache_dir(project_dir)
    run_cache = cache_dir / f"run_{uuid.uuid4().hex[:12]}"
    if cleanup_runtime_cache and run_cache.exists():
        shutil.rmtree(run_cache)
    run_cache.mkdir(parents=True, exist_ok=True)
    test_path = run_cache / "write_test.tmp"
    test_path.write_text("ok", encoding="utf-8")
    cache_write_test_passed = test_path.read_text(encoding="utf-8") == "ok"
    project_inside_onedrive = "onedrive" in str(project_dir).lower()
    try:
        usage = shutil.disk_usage(run_cache)
        free_mb = int(usage.free / (1024 * 1024))
    except Exception:
        free_mb = None
    return {
        "runtime_cache_dir": str(run_cache),
        "project_inside_onedrive": project_inside_onedrive,
        "cache_write_test_passed": cache_write_test_passed,
        "cache_free_space_mb": free_mb,
        "cleanup_performed": False,
    }

