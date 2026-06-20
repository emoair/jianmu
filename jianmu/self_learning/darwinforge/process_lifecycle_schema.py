from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from jianmu.self_learning.darwinforge.architecture_finalization_schema import PROFILE_NAME
from jianmu.self_learning.darwinforge.redqueen_iteration_schema import STILL_NOT_PROVEN_ITERATION


PROCESS_NAMES_COMPILER: Tuple[str, ...] = ("cl.exe", "link.exe")
PROCESS_NAMES_GIT: Tuple[str, ...] = ("git.exe",)


@dataclass(frozen=True)
class ProcessLifecycleConfig:
    profile_name: str = PROFILE_NAME
    idle_grace_seconds: int = 30
    max_lingering_python_children: int = 0
    max_lingering_git_processes: int = 0
    max_lingering_compiler_processes: int = 0
    max_active_worker_threads: int = 0
    allow_main_thread_only: bool = True
    events: int = 20_000
    minimum_real_compiler_invocations: int = 10_000
    workers: int = 16
    compiler_workers: int = 16
    require_plan_follow_rate: float = 0.95


STILL_NOT_PROVEN_LIFECYCLE: Tuple[str, ...] = STILL_NOT_PROVEN_ITERATION
