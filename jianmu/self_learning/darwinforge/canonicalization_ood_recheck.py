from __future__ import annotations

from typing import Dict, List

from jianmu.self_learning.darwinforge.canonicalization_ood_audit import run_canonicalization_ood_audit


def run_canonicalization_ood_recheck(samples: List[Dict], slice_source: str = "v0_8_3_selected_ood_slice") -> Dict:
    audit = run_canonicalization_ood_audit(samples)
    count = audit.get("canonicalizer_made_supported_count", 0)
    if count == 0:
        reason = "not_reproduced; likely slice mismatch or detector mismatch against v0.8.1 guard-stress reason"
    else:
        reason = ""
    summary = {key: value for key, value in audit.items() if key != "records"}
    summary.update(
        {
            "canonicalizer_audit_slice_source": slice_source,
            "compared_to_v0_8_1_reason": "v0.8.1 reported canonicalizer_made_it_look_supported as most_common_false_accept_reason",
            "reason_not_reproduced": reason,
            "records": audit["records"],
        }
    )
    return summary

