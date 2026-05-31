from __future__ import annotations

from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_autopsy import build_contrastive_pair_audit


def audit_redqueen_contrastive_pairs(inputs: Dict[str, Any], pattern_roi: Dict[str, Any]) -> Dict[str, Any]:
    return build_contrastive_pair_audit(inputs, pattern_roi)
