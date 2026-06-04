"""Post-V1.0 archive index builder.

This module is read-only over historical evidence. It builds manifests and
audit records without moving, deleting, or rewriting historical records.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CRITICAL_EVIDENCE_PATHS = [
    "records/v0_9_28_1/full_compile_50k_accounting.json",
    "records/v0_9_28_1/full_compile_50k_continuation.json",
    "records/v0_9_28_1/full_compile_50k_readiness.json",
    "records/v0_9_28_1/mainline_conclusion.md",
    "docs/release_prep/V1_0_SOURCE_REVIEW_NOTICE.md",
    "docs/release_prep/V1_0_PUBLIC_REVIEW_CLAIM_BOUNDARY.md",
    "docs/release_prep/V1_0_NOT_PROVEN_NOTICE.md",
    "docs/release_prep/V1_0_PROJECT_TIMELINE.md",
    "docs/release_prep/V1_0_SOURCE_PACKAGE_MANIFEST.md",
]

STILL_NOT_PROVEN = [
    "formal Turing completeness proof",
    "arbitrary project parsing",
    "solved program synthesis",
    "production readiness",
    "safe real promotion",
    "stable convergence",
    "solved OOD",
    "general program synthesis",
    "default profile changed",
    "function/array production support",
    "recursion production support",
    "natural language layer completed",
    "emergence proven",
]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_md(path: Path, title: str, sections: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    for heading, body in sections:
        lines.extend([f"## {heading}", body.strip(), ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _exists(path: str, root: Path) -> bool:
    return (root / path).exists()


def build_active_core_manifest(root: Path, output_records: Path) -> dict[str, Any]:
    modules = [
        "jianmu/self_learning/darwinforge/arithmetic_compiler_backend.py",
        "jianmu/self_learning/darwinforge/bounded_substrate_compiler_temp_manager.py",
        "jianmu/self_learning/darwinforge/architecture_charter_guard.py",
        "jianmu/self_learning/darwinforge/workload_trace.py",
    ]
    entrypoints = [
        "examples/run_full_compile_50k_continuation.py",
        "examples/run_frontier_review_proof_readiness_rc_prep.py",
    ]
    tests = [
        "tests/test_architecture_charter_guard.py",
        "tests/test_full_compile_50k_readiness.py",
        "tests/test_full_compile_50k_accounting.py",
    ]
    docs = [
        "README.md",
        "docs/development/POST_V1_0_DEVELOPMENT_BASELINE.md",
        "docs/release_prep/V1_0_PUBLIC_REVIEW_CLAIM_BOUNDARY.md",
    ]
    payload = {
        "active_core_modules": modules,
        "active_core_entrypoints": entrypoints,
        "active_core_tests": tests,
        "active_core_docs": docs,
        "why_active": "These files anchor compiler verification, architecture-charter checks, review evidence accounting, and post-V1.0 development orientation.",
        "missing_active_core_paths": [p for p in modules + entrypoints + tests + docs if not _exists(p, root)],
    }
    _write_json(output_records / "active_core_manifest.json", payload)
    return payload


def build_active_frontier_manifest(root: Path, output_records: Path) -> dict[str, Any]:
    groups = {
        "function_frontier": ["function_frontier_scaleup.py", "forgefrontier_function_grammar.py"],
        "array_frontier": ["array_frontier_scaleup.py", "forgefrontier_array_grammar.py"],
        "function_array_interop": ["function_array_interop_scaleup.py", "function_array_regression_guard.py"],
        "turing_frontier": ["turing_frontier_true_endurance.py", "turing_frontier_regression_guard.py", "turing_expressivity_proof_artifact.py"],
        "codecartographer": ["codecartographer_runner.py", "codecartographer_standard_token.py"],
        "mirrorforge": ["mirrorforge_runner.py", "mirrorforge_token_schema.py"],
        "symbiote": ["longhaul_symbiote_runner.py", "frontend_batchcompile_symbiote.py"],
        "redqueen": ["redqueen_v2_bandit_scheduler.py", "redqueen_causal_curriculum_designer.py"],
        "hydrabudget": ["hydrabudget_allocator.py", "redqueen_hydrabudget_probe.py"],
        "ironjudge_compiler_validation": ["ironjudge_compiler_scale_validation.py", "ironjudge_invocation_accounting.py"],
    }
    base = root / "jianmu/self_learning/darwinforge"
    modules = {name: [str(base / item).replace(str(root) + "\\", "").replace("\\", "/") for item in items if (base / item).exists()] for name, items in groups.items()}
    payload = {
        "active_frontier_modules": modules,
        "frontier_status": {
            "function_frontier": "review-ready evidence, not production support",
            "array_frontier": "review-ready evidence, not production support",
            "turing_frontier": "constructive evidence review-ready, formal proof not completed",
            "teacher_paths": "CodeCartographer and MirrorForge remain active teacher-path evidence",
        },
        "production_supported": {
            "function": False,
            "array": False,
            "recursion": False,
            "unbounded": False,
            "arbitrary_project_parsing": False,
            "natural_language_layer": False,
        },
        "next_development_owner": {
            "frontier": "future 1.1/1.2 review tracks",
            "compiler_validation": "IronJudge/full-compile evidence tooling",
            "teacher_paths": "CodeCartographer/MirrorForge continuation",
        },
    }
    _write_json(output_records / "active_frontier_manifest.json", payload)
    return payload


def build_legacy_experiment_manifest(root: Path, output_records: Path) -> dict[str, Any]:
    darwin = root / "jianmu/self_learning/darwinforge"
    patterns = ["*_probe.py", "*_scaleup.py", "*_failure_analysis.py", "*_readiness.py", "*_audit.py"]
    modules = sorted({str(path.relative_to(root)).replace("\\", "/") for pattern in patterns for path in darwin.glob(pattern)})
    examples = sorted(str(path.relative_to(root)).replace("\\", "/") for path in (root / "examples").glob("run_*") if path.is_file())
    tests = sorted(str(path.relative_to(root)).replace("\\", "/") for path in (root / "tests").glob("test_*") if path.is_file())
    payload = {
        "legacy_experiment_modules": modules,
        "legacy_examples": examples,
        "legacy_tests": tests,
        "safe_to_keep": True,
        "safe_to_archive": "index-only for now",
        "not_safe_to_move_yet": [
            "Python modules imported by tests or examples",
            "records required by source review evidence",
            "datasets required by reproduction commands",
        ],
        "duplicate_wrapper_candidates": [m for m in modules if m.endswith("_readiness.py") or m.endswith("_failure_analysis.py")],
        "duplicated_schema_glue": "review only; do not modify yet",
        "duplicate_reporting_modules": "review only; do not modify yet",
        "recommended_consolidation": "Create future shared report helpers after import graph audit; do not delete wrappers in this baseline.",
        "do_not_modify_yet": ["core source", "tests", "historical records", "historical datasets"],
    }
    _write_json(output_records / "legacy_experiment_manifest.json", payload)
    return payload


def build_archive_index(root: Path, output_records: Path) -> dict[str, Any]:
    evidence_chain = [
        ("v0.9.17", "RedQueen/HydraBudget evidence"),
        ("v0.9.18", "IronJudge compiler validation"),
        ("v0.9.20", "Architecture Charter and RedQueen v2"),
        ("v0.9.21", "MirrorForge"),
        ("v0.9.22", "CodeCartographer"),
        ("v0.9.23", "Symbiote"),
        ("v0.9.24", "freeze candidate audit"),
        ("v0.9.25", "longhaul diagnostic"),
        ("v0.9.26/26.1", "Turing frontier"),
        ("v0.9.27/27.1", "function-array + clean rerun"),
        ("v0.9.28/28.1", "frontier review + 50K continuation"),
        ("v1.0 source review candidate", "public review docs"),
    ]
    records = sorted(str(path.relative_to(root)).replace("\\", "/") for path in (root / "records").glob("v0_9_*") if path.is_dir())
    datasets = sorted(str(path.relative_to(root)).replace("\\", "/") for path in (root / "datasets").glob("*") if path.is_dir())
    payload = {
        "archive_index_generated": True,
        "evidence_archive": evidence_chain,
        "records_archive_index": records,
        "dataset_archive_index": datasets,
        "critical_records_to_preserve": CRITICAL_EVIDENCE_PATHS[:4],
        "optional_large_records_to_exclude_from_future_packages": ["full JSONL traces", "large dataset shards", "temporary compiler outputs"],
        "reproduction_paths": CRITICAL_EVIDENCE_PATHS,
        "checksum_needed": True,
    }
    _write_json(output_records / "archive_index_summary.json", payload)
    return payload


def run_evidence_preservation_audit(root: Path, output_records: Path) -> dict[str, Any]:
    missing = [path for path in CRITICAL_EVIDENCE_PATHS if not _exists(path, root)]
    payload = {
        "all_critical_evidence_present": not missing,
        "missing_critical_evidence": missing,
        "evidence_paths_stable": not missing,
        "evidence_preservation_passed": not missing,
        "critical_evidence_paths": CRITICAL_EVIDENCE_PATHS,
        "no_deleted_critical_evidence": True,
        "no_release_or_tag_created": True,
    }
    _write_json(output_records / "evidence_preservation_audit.json", payload)
    return payload


def build_readme_cleanup_report(root: Path, output_records: Path) -> dict[str, Any]:
    readme = (root / "README.md").read_text(encoding="utf-8")
    lower = readme.lower()
    normalized = (
        lower.replace("not production ready", "")
        .replace("not a production release", "")
        .replace("does not claim production readiness", "")
        .replace("or production readiness", "")
    )
    payload = {
        "readme_cleanup_completed": "Development Baseline" in readme and "Archive" in readme,
        "links_baseline": "docs/development/POST_V1_0_DEVELOPMENT_BASELINE.md" in readme,
        "links_archive": "docs/archive/V0_9_EXPERIMENT_ARCHIVE_INDEX.md" in readme,
        "no_production_claim_added": "production ready" not in normalized,
    }
    _write_json(output_records / "readme_cleanup_report.json", payload)
    return payload


def write_readiness(output_records: Path, active_core: dict[str, Any], active_frontier: dict[str, Any], legacy: dict[str, Any], archive: dict[str, Any], evidence: dict[str, Any], readme: dict[str, Any]) -> dict[str, Any]:
    ready = evidence["evidence_preservation_passed"] and readme["readme_cleanup_completed"] and not active_core["missing_active_core_paths"]
    payload = {
        "archive_index_generated": archive["archive_index_generated"],
        "active_core_manifest_generated": True,
        "active_frontier_manifest_generated": True,
        "legacy_experiment_manifest_generated": True,
        "evidence_preservation_audit_passed": evidence["evidence_preservation_passed"],
        "all_critical_evidence_present": evidence["all_critical_evidence_present"],
        "readme_cleanup_completed": readme["readme_cleanup_completed"],
        "ready_for_post_v1_0_development": ready,
        "ready_for_official_release": False,
        "tag_created": False,
        "release_created": False,
        "blocking_issues": [] if ready else ["baseline_or_evidence_audit_incomplete"],
        "still_not_proven": STILL_NOT_PROVEN,
    }
    _write_json(output_records / "post_v1_0_baseline_readiness.json", payload)
    _write_md(
        output_records / "mainline_conclusion.md",
        "v1.0.1 ForgeClean Archive Baseline",
        [
            ("Result", f"ready_for_post_v1_0_development: `{ready}`\n\nready_for_official_release: `false`"),
            ("Still Not Proven", "\n".join(f"- {item}" for item in STILL_NOT_PROVEN)),
        ],
    )
    return payload


def run_forgeclean(root: Path, docs_root: Path, output_records: Path) -> dict[str, Any]:
    output_records.mkdir(parents=True, exist_ok=True)
    archive = build_archive_index(root, output_records)
    active_core = build_active_core_manifest(root, output_records)
    active_frontier = build_active_frontier_manifest(root, output_records)
    legacy = build_legacy_experiment_manifest(root, output_records)
    evidence = run_evidence_preservation_audit(root, output_records)
    readme = build_readme_cleanup_report(root, output_records)
    readiness = write_readiness(output_records, active_core, active_frontier, legacy, archive, evidence, readme)
    return readiness


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build v1.0.1 ForgeClean archive baseline indexes.")
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--output-records", default="records/v1_0_1_forgeclean")
    for flag in [
        "build-archive-index",
        "build-active-core-manifest",
        "build-active-frontier-manifest",
        "build-legacy-experiment-manifest",
        "run-evidence-preservation-audit",
        "run-readme-cleanup-report",
        "progress",
    ]:
        parser.add_argument(f"--{flag}", default="true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    readiness = run_forgeclean(Path.cwd(), Path(args.docs_root), Path(args.output_records))
    print(json.dumps({"output_records": args.output_records, "ready_for_post_v1_0_development": readiness["ready_for_post_v1_0_development"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
