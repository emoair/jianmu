from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict


def build_reviewer_evidence_bundle(output_records: str | Path, readiness_inputs: Dict[str, object]) -> Dict[str, object]:
    out = Path(output_records)
    bundle = out / "reviewer_evidence_bundle"
    bundle.mkdir(parents=True, exist_ok=True)
    sample_src = out / "review_samples"
    sample_dst = bundle / "review_samples"
    if sample_dst.exists():
        shutil.rmtree(str(sample_dst))
    if sample_src.exists():
        shutil.copytree(str(sample_src), str(sample_dst))
    _write(bundle / "REVIEWER_README.md", _readme())
    _write(bundle / "REVIEW_CHECKLIST.md", _checklist())
    _write(bundle / "CLAIM_BOUNDARY_SUMMARY.md", _claim_boundary())
    _write(bundle / "EVIDENCE_INDEX.md", _evidence_index())
    _write(bundle / "POLICY_PATH_MAP.md", _policy_map())
    _write(bundle / "TRACE_REPLAY_SUMMARY.md", _summary("Trace Replay Summary", readiness_inputs.get("trace_replay_validation", {})))
    _write(bundle / "INTERFACE_LANDING_REVIEW.md", _summary("Interface Landing Review", readiness_inputs.get("interface_landing_review", {})))
    _write(bundle / "REVIEW_SAMPLE_INDEX.md", _sample_index(out / "review_sample_manifest.jsonl"))
    manifest = _artifact_manifest(bundle)
    (bundle / "artifact_sha256_manifest.json").write_text(json.dumps({"artifacts": manifest}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = {"reviewer_evidence_bundle_generated": True, "artifact_sha256_manifest_generated": True, "bundle_path": str(bundle), "bundle_artifact_count": len(manifest)}
    (bundle / "bundle_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _readme() -> str:
    return """# Reviewer Evidence Bundle

This bundle shows that the v1.0.5.1 experimental active bridge can be sampled and replayed through policy, builder, ExtendedIR, ExtendedEmitterC, C source, cl.exe compile/link, executable run, and stdout comparison.

It does not prove production function support, production array support, production recursion support, production readiness, formal Turing completeness, solved synthesis, or natural language completion.

To inspect it, open `REVIEW_SAMPLE_INDEX.md`, choose samples, inspect `review_samples/<id>/emitted.c`, compare expected and actual stdout, then check `TRACE_REPLAY_SUMMARY.md`.

Allowed claim: human-review-ready experimental active bridge evidence. Forbidden claim: production support completed.
"""


def _checklist() -> str:
    return """# Review Checklist

- [ ] policy path exists
- [ ] ExtendedIR present
- [ ] ExtendedEmitterC generated C
- [ ] cl.exe actually invoked
- [ ] stdout matches
- [ ] trace replay passes
- [ ] no template bypass
- [ ] no production overclaim
"""


def _claim_boundary() -> str:
    return """# Claim Boundary Summary

Production support remains false for functions, arrays, and recursion. This bundle is for human review before any production-profile dry-run candidate.
"""


def _evidence_index() -> str:
    return """# Evidence Index

- `INTERFACE_LANDING_REVIEW.md`
- `TRACE_REPLAY_SUMMARY.md`
- `POLICY_PATH_MAP.md`
- `REVIEW_SAMPLE_INDEX.md`
- `review_samples/`
- `artifact_sha256_manifest.json`
"""


def _policy_map() -> str:
    return """# Policy Path Map

- canonical_arithmetic_targetir -> existing arithmetic backend -> compiler/stdout
- canonical_function_targetir -> build_function_program -> FunctionCallProgram -> ExtendedEmitterC
- canonical_array_targetir -> build_array_program -> ArrayProgram -> ExtendedEmitterC
- canonical_function_array_targetir -> build_function_array_program -> FunctionArrayProgram -> ExtendedEmitterC
- canonical_structured_recursion_targetir -> build_factorial_program -> RecursiveFunctionProgram -> ExtendedEmitterC
- mixed_extended_ir_path -> deterministic mixed ExtendedIR builders -> ExtendedEmitterC
"""


def _summary(title: str, payload: object) -> str:
    return "# " + title + "\n\n```json\n" + json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n```\n"


def _sample_index(path: Path) -> str:
    if not path.exists():
        return "# Review Sample Index\n\nNo samples found.\n"
    lines = ["# Review Sample Index", ""]
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if idx >= 300:
            break
        row = json.loads(line)
        lines.append(f"- `{row['review_sample_id']}` {row['policy']} {row['ir_kind']} original_passed={row['original_passed']}")
    return "\n".join(lines) + "\n"


def _artifact_manifest(root: Path):
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.name == "artifact_sha256_manifest.json":
            continue
        rows.append({"path": str(path.relative_to(root)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "size_bytes": path.stat().st_size})
    return rows


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")

