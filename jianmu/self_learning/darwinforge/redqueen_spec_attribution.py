from __future__ import annotations

from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_autopsy import build_spec_attribution


def compute_redqueen_spec_attribution(inputs: Dict[str, Any]) -> Dict[str, Any]:
    return build_spec_attribution(inputs)
