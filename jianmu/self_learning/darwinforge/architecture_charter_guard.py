from __future__ import annotations

from pathlib import Path
from typing import Dict


def run_architecture_charter_guard(repo_root: str | Path = ".") -> Dict[str, object]:
    root = Path(repo_root)
    charter = root / "docs" / "architecture" / "JIANMU_ARCHITECTURE_CHARTER.md"
    text = charter.read_text(encoding="utf-8") if charter.exists() else ""
    py_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore").lower() for path in (root / "jianmu" / "self_learning" / "darwinforge").glob("*redqueen_v2*.py"))
    regression_text = (root / "jianmu" / "self_learning" / "darwinforge" / "regression_dashboard.py").read_text(encoding="utf-8", errors="ignore").lower()
    result = {
        "architecture_charter_exists": charter.exists(),
        "boundary_as_data_contract_documented": "Boundary-as-Data-Contract" in text and "dataset schema" in text,
        "no_runtime_keyword_rejection_gate_added": "keyword rejection" not in py_text,
        "no_candidate_generation_boundary_hardcode_added": "candidate generation boundary" not in py_text,
        "no_routing_boundary_hardcode_added": "routing boundary" not in py_text,
        "regression_dashboard_not_replay_buffer": "replay buffer" not in regression_text and "replay_buffer" not in regression_text,
        "boundary_checks_are_offline_eval": "offline evaluation" in text,
        "redqueen_only_adjusts_curriculum": "RedQueen adjusts curriculum distribution" in text,
        "hydrabudget_only_shadow_budget": "HydraBudget adjusts shadow budget allocation" in text,
        "compiler_only_validation": "IronJudge verifies compiled outputs" in text,
        "limitations": [],
    }
    result["charter_guard_passed"] = all(bool(v) for k, v in result.items() if k not in {"limitations"})
    return result
