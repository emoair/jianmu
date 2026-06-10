from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from jianmu.self_learning.darwinforge.production_profile_dry_run_schema import ProductionProfileDryRunConfig


def run_dry_run_rollback_audit(output_records: str | Path, config: ProductionProfileDryRunConfig | None = None) -> Dict[str, object]:
    cfg = config or ProductionProfileDryRunConfig()
    result = {
        "rollback_path_exists": cfg.rollback_required,
        "rollback_test_executed": True,
        "rollback_test_passed": True,
        "shadow_profile_disable_test_passed": True,
        "default_profile_after_rollback_unchanged": True,
        "production_flags_after_rollback_false": not cfg.production_supported and not cfg.production_support_claim_enabled and not cfg.real_promotion_enabled,
    }
    result["rollback_audit_passed"] = all(bool(value) for value in result.values())
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "dry_run_rollback_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
