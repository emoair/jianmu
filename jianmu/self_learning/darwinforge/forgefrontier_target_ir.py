from __future__ import annotations

from typing import Any, Dict


def make_frontier_target_ir(kind: str, stdout: int) -> Dict[str, Any]:
    if kind not in {"forge_function", "forge_array", "forge_function_array"}:
        raise ValueError(f"unsupported frontier target kind: {kind}")
    return {"kind": kind, "version": 1, "stdout": int(stdout)}
