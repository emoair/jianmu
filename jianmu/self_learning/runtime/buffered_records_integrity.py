from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable


def check_buffered_records_integrity(records: Iterable[Dict], expected_sample_ids: Iterable[str]) -> Dict:
    rows = list(records)
    expected = set(expected_sample_ids)
    ids = [row.get("sample_id") for row in rows if row.get("sample_id")]
    counts = Counter(ids)
    duplicates = sorted(sample_id for sample_id, count in counts.items() if count > 1)
    missing = sorted(expected - set(ids))
    return {
        "duplicate_record_count": len(duplicates),
        "missing_record_count": len(missing),
        "duplicate_sample_ids": duplicates[:20],
        "missing_sample_ids": missing[:20],
        "shard_count": len(set(row.get("worker_id") for row in rows)),
        "merge_integrity_passed": not duplicates and not missing,
        "total_record_count": len(rows),
    }

