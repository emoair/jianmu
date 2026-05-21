from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List

from jianmu.self_learning.darwinforge.ood_precision_audit import run_ood_precision_audit, summarize_ood_precision


@dataclass
class OODPrecisionAuditConfig:
    max_examples_per_class: int = 20
    include_raw_and_canonical: bool = True
    include_reason: bool = True


def run_ood_precision_recheck(samples: List[Dict], guard_records: List[Dict], config: OODPrecisionAuditConfig = None) -> Dict:
    config = config or OODPrecisionAuditConfig()
    audit = run_ood_precision_audit(samples, guard_records)
    examples = defaultdict(list)
    for row in audit["records"]:
        label = row.get("precision_label", "unknown")
        if len(examples[label]) < config.max_examples_per_class:
            examples[label].append(row)
    summary = summarize_ood_precision(audit["records"])
    return {
        **summary,
        "examples_by_precision_label": dict(examples),
        "beneficial_generalization_candidate_count": summary.get("near_ood_generalization_candidate_count", 0),
        "dangerous_false_accept_count": summary.get("true_false_accept_count", 0),
        "records": audit["records"],
    }

