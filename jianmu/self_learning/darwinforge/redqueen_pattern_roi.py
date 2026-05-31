from __future__ import annotations

from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_autopsy import build_pattern_roi


def compute_redqueen_pattern_roi(inputs: Dict[str, Any], spec_attribution: Dict[str, Any]) -> Dict[str, Any]:
    return build_pattern_roi(inputs, spec_attribution)
