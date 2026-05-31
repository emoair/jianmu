from __future__ import annotations

from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_autopsy import build_template_overfit_audit


def audit_redqueen_template_overfit(inputs: Dict[str, Any]) -> Dict[str, Any]:
    return build_template_overfit_audit(inputs)
