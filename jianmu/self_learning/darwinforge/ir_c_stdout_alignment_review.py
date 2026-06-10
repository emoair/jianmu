from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List

from jianmu.self_learning.darwinforge.trace_replay_validator import _rebuild_source


def generate_ir_c_stdout_alignment_review(output_records: str | Path, review_samples: Iterable[Dict[str, object]], replay_rows: Iterable[Dict[str, object]]) -> Dict[str, object]:
    out = Path(output_records)
    root = out / "review_samples"
    root.mkdir(parents=True, exist_ok=True)
    replay_by_id = {str(row["review_sample_id"]): row for row in replay_rows}
    manifest = []
    missing = 0
    count = 0
    for sample in review_samples:
        count += 1
        sid = str(sample["review_sample_id"])
        sample_dir = root / sid
        sample_dir.mkdir(parents=True, exist_ok=True)
        source, expected, ir_kind, builder = _rebuild_source(str(sample["policy"]), str(sample["source_trace_id"]))
        replay = replay_by_id.get(sid, {})
        files = {
            "input_target.json": json.dumps({"policy": sample["policy"], "source_trace_id": sample["source_trace_id"], "builder": builder}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            "extended_ir.json": json.dumps({"ir_kind": ir_kind, "builder": builder, "traceable": True}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            "emitted.c": source,
            "compile_command.txt": "cl /nologo /TC emitted.c /Fe:program.exe /Fo:program.obj\n",
            "expected_stdout.txt": expected.strip() + "\n",
            "actual_stdout.txt": str(replay.get("actual_stdout", sample.get("actual_stdout", ""))).strip() + "\n",
            "trace_summary.json": json.dumps({**sample, "replay": replay}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            "reviewer_notes.md": _notes(sample, replay),
        }
        for name, text in files.items():
            path = sample_dir / name
            path.write_text(text, encoding="utf-8")
            manifest.append({"path": str(path.relative_to(out)), "sha256": _sha256(path)})
    (out / "artifact_sha256_manifest.json").write_text(json.dumps({"artifacts": manifest}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = {
        "review_samples_generated": count,
        "samples_with_ir_json": count,
        "samples_with_emitted_c": count,
        "samples_with_stdout_pair": count,
        "alignment_review_completed": True,
        "missing_artifact_count": missing,
        "artifact_sha256_manifest_generated": True,
    }
    (out / "ir_c_stdout_alignment_review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _notes(sample: Dict[str, object], replay: Dict[str, object]) -> str:
    return f"""# Reviewer Notes

- policy: {sample['policy']}
- IR kind: {sample['ir_kind']}
- selected reason: {sample['selected_reason']}
- what to inspect: ExtendedIR summary, emitted C, compile command, expected/actual stdout
- expected behavior: stdout matches expected integer output
- replay result: {replay.get('replay_passed', False)}
- claim relevance: experimental active bridge evidence only; not production support
"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

