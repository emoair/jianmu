from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.extended_emitter_c import ExtendedEmitterC
from jianmu.self_learning.darwinforge.atomic_synthesis_policy_bridge import build_extended_target
from jianmu.self_learning.darwinforge.production_path_reconciliation_schema import EXPERIMENTAL_POLICIES


def trace_policy_path(policy: str, value: int = 7) -> Dict[str, Any]:
    canonical, source, expected, meta = build_extended_target(policy, {"signed_numbers": [value]})
    return {
        "target_builder_policy": policy,
        "builder": f"{EXPERIMENTAL_POLICIES.get(policy, 'unknown')}_builder",
        "extended_ir": True,
        "ir_kind": EXPERIMENTAL_POLICIES.get(policy, "unknown"),
        "emitter": "ExtendedEmitterC",
        "c_source_generated": bool(source and "#include <stdio.h>" in source),
        "source_sha256": _hash(source),
        "expected_stdout": expected,
        "canonical": canonical,
        "metadata": meta,
    }


def trace_all_policy_paths(output_records: str | Path = None) -> List[Dict[str, Any]]:
    rows = [trace_policy_path(policy, index + 5) for index, policy in enumerate(EXPERIMENTAL_POLICIES)]
    if output_records is not None:
        path = Path(output_records) / "policy_path_coverage.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"policy_path_trace_generated": True, "paths": rows}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rows


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

