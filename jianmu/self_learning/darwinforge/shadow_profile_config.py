from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from jianmu.self_learning.darwinforge.production_profile_dry_run_schema import ProductionProfileDryRunConfig


def build_shadow_profile_config(output_records: str | Path, config: ProductionProfileDryRunConfig | None = None) -> Dict[str, object]:
    cfg = config or ProductionProfileDryRunConfig()
    result = {
        "shadow_profile_created": True,
        "profile_name": cfg.profile_name,
        "explicitly_opt_in": cfg.explicitly_opt_in,
        "default_profile": cfg.default_profile,
        "default_profile_unchanged": True,
        "real_promotion_enabled": cfg.real_promotion_enabled,
        "user_facing_enabled": cfg.user_facing_enabled,
        "release_enabled": cfg.release_enabled,
        "production_support_claim_enabled": cfg.production_support_claim_enabled,
        "production_supported": cfg.production_supported,
        "dry_run_enabled": cfg.dry_run_enabled,
        "experimental_active_bridge": cfg.experimental_active_bridge,
        "rollback_required": cfg.rollback_required,
        "audit_trace_required": cfg.audit_trace_required,
        "compiler_validation_required": cfg.compiler_validation_required,
        "enabled_policies": list(cfg.enabled_policies),
        "disabled_policies": list(cfg.disabled_policies),
        "rollback_mode": "disable_shadow_profile_without_touching_default",
        "claim_boundary": cfg.claim_boundary(),
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "shadow_profile_config.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
