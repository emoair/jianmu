from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from jianmu.self_learning.darwinforge.staged_opt_in_profile_schema import StagedOptInProfileConfig


def build_staged_opt_in_config(output_records: str | Path, config: StagedOptInProfileConfig | None = None) -> Dict[str, object]:
    cfg = config or StagedOptInProfileConfig()
    result = {
        "staged_opt_in_profile_created": True,
        "profile_name": cfg.profile_name,
        "explicitly_opt_in": cfg.explicitly_opt_in,
        "default_profile": cfg.default_profile,
        "default_profile_unchanged": cfg.default_profile_unchanged,
        "real_promotion_enabled": cfg.real_promotion_enabled,
        "user_facing_enabled": cfg.user_facing_enabled,
        "official_release_enabled": cfg.official_release_enabled,
        "production_support_claim_enabled": cfg.production_support_claim_enabled,
        "opt_in_enabled_only_by_explicit_flag": cfg.opt_in_enabled_only_by_explicit_flag,
        "opt_out_supported": cfg.opt_out_supported,
        "rollback_required": cfg.rollback_required,
        "audit_trace_required": cfg.audit_trace_required,
        "compiler_validation_required": cfg.compiler_validation_required,
        "production_supported": cfg.production_supported,
        "staged_opt_in_candidate": cfg.staged_opt_in_candidate,
        "experimental_active_bridge": cfg.experimental_active_bridge,
        "enabled_policies": list(cfg.enabled_policies),
        "disabled_policies": list(cfg.disabled_policies),
        "rollback_mode": "disable_explicit_opt_in_profile_without_touching_default",
        "claim_boundary": cfg.claim_boundary(),
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "staged_opt_in_config.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
