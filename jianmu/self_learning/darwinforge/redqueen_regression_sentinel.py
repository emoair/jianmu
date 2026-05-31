from __future__ import annotations

from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_autopsy import build_regression_sentinel


def run_redqueen_regression_sentinel(inputs: Dict[str, Any]) -> Dict[str, Any]:
    return build_regression_sentinel(inputs)
