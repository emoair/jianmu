from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.human_review_pack_readiness import build_human_review_pack_readiness
from jianmu.self_learning.darwinforge.human_review_pack_schema import HumanReviewPackConfig
from jianmu.self_learning.darwinforge.ir_c_stdout_alignment_review import generate_ir_c_stdout_alignment_review
from jianmu.self_learning.darwinforge.production_bridge_interface_review import run_interface_landing_review
from jianmu.self_learning.darwinforge.production_dry_run_precheck import write_production_dry_run_precheck
from jianmu.self_learning.darwinforge.reviewer_evidence_bundle_builder import build_reviewer_evidence_bundle
from jianmu.self_learning.darwinforge.trace_replay_validator import run_trace_replay_validation
from jianmu.self_learning.darwinforge.trace_sampling_strategy import select_replay_samples, select_review_samples


def main() -> None:
    args = parse_args()
    out = Path(args.output_records)
    out.mkdir(parents=True, exist_ok=True)
    config = HumanReviewPackConfig(total_review_samples=int(args.review_samples), replay_validation_samples=int(args.replay_validation_samples), replay_minimum_required=int(args.replay_minimum_required), workers=int(args.workers), compiler_workers=int(args.compiler_workers), seed=int(args.seed))
    source_pack = Path(args.source_trace_pack)
    source_found = source_pack.exists()
    trace_replayable = source_found and any(source_pack.glob("policy_path_trace_*.jsonl"))
    interface = run_interface_landing_review(out)
    review_samples = select_review_samples(source_pack, out, config) if trace_replayable else []
    replay_samples = select_replay_samples(source_pack, out, config) if trace_replayable else []
    replay = run_trace_replay_validation(out, replay_samples, workers=config.workers, compiler_workers=config.compiler_workers) if replay_samples else {"replay_validation_completed": False, "replay_sample_count": 0, "replay_fail_count": 1, "workers_requested": config.workers, "workers_used": 0, "downgrade_reason": "source_trace_pack_missing"}
    replay_rows = _load_jsonl(out / "trace_replay_manifest.jsonl")
    alignment = generate_ir_c_stdout_alignment_review(out, review_samples, replay_rows) if review_samples else {"alignment_review_completed": False}
    precheck_probe = write_production_dry_run_precheck(out, False)
    bundle = build_reviewer_evidence_bundle(out, {"trace_replay_validation": replay, "interface_landing_review": interface})
    ready_probe = replay.get("replay_fail_count", 1) == 0 and alignment.get("alignment_review_completed", False) and bundle.get("reviewer_evidence_bundle_generated", False)
    precheck = write_production_dry_run_precheck(out, ready_probe)
    readiness = build_human_review_pack_readiness(out, source_found, trace_replayable, interface, len(review_samples), replay, alignment, bundle, precheck)
    _write_mainline(out / "mainline_conclusion.md", readiness)
    _write_json(out / "mainline_conclusion.json", {"config": config.to_dict(), "readiness": readiness, "interface": interface, "replay": replay, "alignment": alignment, "precheck": precheck})
    print(json.dumps({"output_records": str(out), "recommended_claim_level": readiness["recommended_claim_level"], "replay_success_rate": readiness["replay_success_rate"]}, ensure_ascii=False, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-5-1", default="records/v1_0_5_1_reaudit_scale")
    parser.add_argument("--source-trace-pack", default="records/v1_0_5_1_reaudit_scale/scale_trace_pack")
    parser.add_argument("--output-records", default="records/v1_0_5_2_human_review_pack")
    parser.add_argument("--review-samples", default="300")
    parser.add_argument("--replay-validation-samples", default="1000")
    parser.add_argument("--replay-minimum-required", default="300")
    parser.add_argument("--workers", default="16")
    parser.add_argument("--compiler-workers", default="16")
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    parser.add_argument("--accounting-lock", default="true")
    parser.add_argument("--require-all-policies", default="true")
    parser.add_argument("--run-interface-landing-review", default="true")
    parser.add_argument("--run-trace-sampling", default="true")
    parser.add_argument("--run-trace-replay-validation", default="true")
    parser.add_argument("--run-ir-c-stdout-alignment-review", default="true")
    parser.add_argument("--build-reviewer-evidence-bundle", default="true")
    parser.add_argument("--run-production-dry-run-precheck", default="true")
    parser.add_argument("--run-claim-boundary-review", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--progress", default="true")
    parser.add_argument("--seed", default="197")
    return parser.parse_args()


def _load_jsonl(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_mainline(path: Path, r) -> None:
    still = "\n".join(f"- {item}" for item in r["still_not_proven"])
    blocking = "\n".join(f"- {item}" for item in r["blocking_issues"]) or "- none"
    path.write_text(f"""# V1.0.5.2 Production Bridge Human Review Pack

## What This Version Did

Generated a reviewer-friendly evidence bundle, deterministic samples, replay validation, IR/C/stdout alignment artifacts, interface landing review, and production dry-run precheck.

## What This Version Did Not Do

No production dry-run, no production promotion, no default profile change, no natural language layer, and no new frontier capability.

## Why Human Review Pack

v1.0.5.1 completed 4h scale validation. Before production-profile work, reviewers need evidence they can inspect and replay.

## Results

- source_trace_pack_found: {r['source_trace_pack_found']}
- interface_landing_review_completed: {r['interface_landing_review_completed']}
- atomic_policy_interfaces_valid: {r['atomic_policy_interfaces_valid']}
- extended_ir_interfaces_valid: {r['extended_ir_interfaces_valid']}
- extended_emitter_interfaces_valid: {r['extended_emitter_interfaces_valid']}
- compiler_interfaces_valid: {r['compiler_interfaces_valid']}
- template_bypass_detected: {r['template_bypass_detected']}
- marker_ir_direct_compile_detected: {r['marker_ir_direct_compile_detected']}
- review_sample_count: {r['review_sample_count']}
- replay_success_rate: {r['replay_success_rate']}
- ir_c_stdout_alignment_completed: {r['ir_c_stdout_alignment_completed']}
- reviewer_evidence_bundle_generated: {r['reviewer_evidence_bundle_generated']}
- production_dry_run_executed: {r['production_dry_run_executed']}
- ready_for_production_dry_run_candidate: {r['ready_for_production_dry_run_candidate']}
- production support completed: false
- recommended_claim_level: {r['recommended_claim_level']}

## Blocking Issues

{blocking}

## Required Next Run

{r['required_next_run']}

## Still Not Proven

{still}
""", encoding="utf-8")


def _write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

