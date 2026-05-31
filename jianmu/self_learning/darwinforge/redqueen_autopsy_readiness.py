from __future__ import annotations

from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_autopsy import build_readiness


def build_redqueen_autopsy_readiness(pattern_roi: Dict[str, Any], overfit: Dict[str, Any], contrastive_audit: Dict[str, Any], sentinel: Dict[str, Any], bandit_design: Dict[str, Any]) -> Dict[str, Any]:
    return build_readiness(pattern_roi, overfit, contrastive_audit, sentinel, bandit_design)
