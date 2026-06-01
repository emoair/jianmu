from __future__ import annotations

from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_v2_training_probe import build_readiness


def build_redqueen_v2_readiness(best: Dict[str, Any], evals: Dict[str, Any], audit: Dict[str, Any], policy: Dict[str, Any], dashboard: Dict[str, Any], compiler: Dict[str, Any], charter: Dict[str, Any]) -> Dict[str, Any]:
    return build_readiness(best, evals, audit, policy, dashboard, compiler, charter)
