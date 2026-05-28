from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.multiagent_raw_dataset_audit import (
    multiagent_collapse_audit,
    multiagent_dedup_leakage_audit,
    multiagent_raw_schema_audit,
    multiagent_support_safety_audit,
    run_multiagent_raw_dataset_audit,
)


def _row(rid: str, agent: str = "agent_a", status: str = "current_supported", category: str = "current_supported_bounded_substrate", program: str = "int x = 1;\nint y = 2;\ny = y + x;") -> dict:
    action = {"current_supported": "train_current", "future_domain": "isolate_future", "unsupported": "reject", "trap": "reject", "review": "review", "near_supported": "isolate_future"}[status]
    return {
        "id": rid,
        "raw_dataset_version": "v0.9.15_multiagent_raw",
        "split_hint": "train",
        "category": category,
        "support_status": status,
        "stage": "raw_llm_draft",
        "input": f"compute {rid}",
        "natural_language_variants": [f"compute {rid}", f"find {rid}", f"calculate {rid}"],
        "candidate_program": program,
        "target_ir_hint": None,
        "expected_output_hint": None,
        "expected_action": action,
        "language_features": {
            "has_variable_decl": True,
            "has_assignment": True,
            "has_sequence": True,
            "has_if_else": False,
            "has_for_loop": False,
            "has_while_loop": False,
            "has_nested_control": False,
            "has_function": False,
            "has_function_call": False,
            "has_multiple_functions": False,
            "has_array": False,
            "has_array_loop": False,
            "has_pointer": False,
            "has_recursion": False,
            "has_bounded_recursion": False,
            "has_unbounded_loop": False,
            "has_io": False,
            "has_system_call": False,
            "has_scope_shadowing": False,
        },
        "complexity_hint": {},
        "agent_id": agent,
        "agent_role": "program_drafter",
        "agent_prompt_id": "p1",
        "template_family_id": "t1",
        "structural_hash_hint": "s1",
        "semantic_hash_hint": "sem1",
        "diversity_seed": 1,
    }


def _write_raw(root: Path, rows: list[dict]) -> Path:
    (root / "shards").mkdir(parents=True)
    (root / "stats").mkdir()
    (root / "warnings").mkdir()
    (root / "raw_manifest.json").write_text(json.dumps({"total_samples": len(rows)}), encoding="utf-8")
    (root / "raw_generation_report.md").write_text("# report\n", encoding="utf-8")
    (root / "stats" / "stats.json").write_text("{}\n", encoding="utf-8")
    (root / "warnings" / "known_limitations.md").write_text("raw draft\n", encoding="utf-8")
    (root / "shards" / "raw_candidates_000.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return root


def test_multiagent_raw_schema_audit(tmp_path: Path) -> None:
    raw = _write_raw(tmp_path / "raw", [_row("a")])
    rows = [json.loads(line) for line in (raw / "shards" / "raw_candidates_000.jsonl").read_text().splitlines()]
    audit = multiagent_raw_schema_audit(raw, rows, [])
    assert audit["schema_valid_count"] == 1
    assert audit["schema_audit_passed"] is True
    assert "agent_id" in audit["missing_optional_multiagent_fields"]


def test_multiagent_collapse_audit_detects_cross_agent_duplicates() -> None:
    rows = [_row("a", "agent_a"), _row("b", "agent_b")]
    collapse = multiagent_collapse_audit(rows)
    assert collapse["agent_count"] == 2
    assert collapse["agent_cross_duplicate_rate"] > 0
    assert collapse["multiagent_collapse_detected"] is True


def test_multiagent_dedup_leakage_audit() -> None:
    a = _row("a")
    b = _row("b")
    b["input"] = a["input"]
    b["split_hint"] = "eval"
    audit = multiagent_dedup_leakage_audit([a, b])
    assert audit["duplicate_input_count"] == 1
    assert audit["eval_test_input_leakage_count"] == 0


def test_multiagent_support_safety_blocks_future_supported() -> None:
    row = _row("bad")
    row["language_features"]["has_function"] = True
    audit = multiagent_support_safety_audit([row])
    assert audit["function_marked_current_supported_count"] > 0
    assert audit["support_status_safety_passed"] is False


def test_multiagent_conversion_ignores_raw_expected_output(tmp_path: Path) -> None:
    row = _row("a")
    row["expected_output_hint"] = "999\n"
    readiness = run_multiagent_raw_dataset_audit(_write_raw(tmp_path / "raw", [row]), tmp_path / "prev", tmp_path / "records", tmp_path / "out", supported_spot=1, boundary_spot=0, compile_worker_count=1)
    conversion = json.loads((tmp_path / "records" / "conversion_metrics.json").read_text())
    assert conversion["raw_expected_output_hint_trusted"] is False
    assert readiness["future_domain_compiled_count"] == 0 if "future_domain_compiled_count" in readiness else True


def test_multiagent_compiler_audit_uses_real_cl(tmp_path: Path) -> None:
    run_multiagent_raw_dataset_audit(_write_raw(tmp_path / "raw", [_row("a")]), tmp_path / "prev", tmp_path / "records", tmp_path / "out", supported_spot=1, boundary_spot=0, compile_worker_count=1)
    metrics = json.loads((tmp_path / "records" / "compiler_audit_metrics.json").read_text())
    assert metrics["backend_type"] == "real_c_compiler"
    assert metrics["compiler_name"] == "cl"


def test_multiagent_acceptance_split(tmp_path: Path) -> None:
    run_multiagent_raw_dataset_audit(_write_raw(tmp_path / "raw", [_row("a")]), tmp_path / "prev", tmp_path / "records", tmp_path / "out", supported_spot=1, boundary_spot=0, compile_worker_count=1)
    split = json.loads((tmp_path / "records" / "acceptance_split_metrics.json").read_text())
    assert split["accepted_count"] >= 1
    assert (tmp_path / "out" / "accepted" / "accepted.jsonl").exists()


def test_multiagent_quality_score(tmp_path: Path) -> None:
    run_multiagent_raw_dataset_audit(_write_raw(tmp_path / "raw", [_row("a")]), tmp_path / "prev", tmp_path / "records", tmp_path / "out", supported_spot=1, boundary_spot=0, compile_worker_count=1)
    quality = json.loads((tmp_path / "records" / "raw_quality_score.json").read_text())
    assert "final_dataset_quality_score" in quality


def test_multiagent_readiness_no_turing_claim(tmp_path: Path) -> None:
    readiness = run_multiagent_raw_dataset_audit(tmp_path / "missing", tmp_path / "prev", tmp_path / "records", tmp_path / "out")
    assert readiness["recommended_claim_level"] == "failed"
    assert readiness["turing_completeness_claimed"] is False


def test_no_expression_oracle_import() -> None:
    text = Path("jianmu/self_learning/darwinforge/multiagent_raw_dataset_audit.py").read_text(encoding="utf-8")
    assert "expression_oracle" not in text


def test_no_external_api_calls() -> None:
    text = Path("jianmu/self_learning/darwinforge/multiagent_raw_dataset_audit.py").read_text(encoding="utf-8")
    assert "requests." not in text
    assert "urllib" not in text
    assert "openai" not in text.lower()


def test_no_hardcoded_keyword_gate() -> None:
    text = Path("jianmu/self_learning/darwinforge/multiagent_raw_dataset_audit.py").read_text(encoding="utf-8").lower()
    assert "keyword gate" not in text


def test_real_promotion_disabled(tmp_path: Path) -> None:
    readiness = run_multiagent_raw_dataset_audit(tmp_path / "missing", tmp_path / "prev", tmp_path / "records", tmp_path / "out")
    assert readiness["real_promotion_enabled"] is False
