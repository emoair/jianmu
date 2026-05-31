from __future__ import annotations

from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_autopsy import build_causal_curriculum_plan


def design_redqueen_causal_curriculum(pattern_roi: Dict[str, Any], contrastive_audit: Dict[str, Any], sentinel: Dict[str, Any]) -> Dict[str, Any]:
    return build_causal_curriculum_plan(pattern_roi, contrastive_audit, sentinel)
