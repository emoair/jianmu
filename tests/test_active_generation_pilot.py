from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.active_generation_pilot import (
    audit_raw_dedup_leakage,
    audit_raw_schema,
    audit_support_status_safety,
    convert_current_supported_rows,
    load_raw_rows,
    run_active_generation_pilot,
)


def _write_raw(root: Path, rows: list[dict]) -> Path:
    (root / "shards").mkdir(parents=True)
    (root / "stats").mkdir()
    (root / "warnings").mkdir()
    (root / "raw_manifest.json").write_text(json.dumps({"total_samples": len(rows)}), encoding="utf-8")
    (root / "raw_generation_report.md").write_text("# report\n", encoding="utf-8")
    (root / "warnings" / "known_limitations.md").write_text("not audited\n", encoding="utf-8")
    (root / "stats" / "stats.json").write_text("{}\n", encoding="utf-8")
    (root / "shards" / "raw_candidates_000.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return root


def _row(rid: str, status: str = "current_supported", category: str = "current_supported_bounded_substrate", program: str | None = None) -> dict:
    features = {
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
    }
    action = {"current_supported": "train_current", "future_domain": "isolate_future", "unsupported": "reject", "trap": "reject", "review": "review", "near_supported": "isolate_future"}[status]
    return {
        "id": rid,
        "raw_dataset_version": "v0.9.15_raw_llm_draft",
        "split_hint": "train",
        "category": category,
        "support_status": status,
        "stage": "raw_llm_draft",
        "input": f"compute {rid}",
        "natural_language_variants": [f"compute {rid}", f"find {rid}", f"calculate {rid}"],
        "candidate_program": program or "int x = 2;\nint y = 3;\ny = y + x;",
        "canonical_program_hint": None,
        "target_ir_hint": None,
        "expected_output_hint": None,
        "expected_action": action,
        "language_features": features,
        "complexity_hint": {},
        "safety_notes": [],
        "generation_notes": {"llm_generated": True},
    }


def test_raw_schema_audit(tmp_path: Path) -> None:
    root = _write_raw(tmp_path / "raw", [_row("a")])
    rows, malformed = load_raw_rows(root)
    audit = audit_raw_schema(root, rows, malformed)
    assert audit["schema_valid_count"] == 1
    assert audit["schema_audit_passed"] is True


def test_raw_support_status_safety() -> None:
    bad = _row("bad")
    bad["language_features"]["has_function"] = True
    audit = audit_support_status_safety([bad])
    assert audit["function_marked_current_supported_count"] == 1
    assert audit["support_status_safety_passed"] is False


def test_raw_dedup_leakage_audit() -> None:
    a = _row("a")
    b = _row("b")
    b["input"] = a["input"]
    b["split_hint"] = "eval"
    audit = audit_raw_dedup_leakage([a, b])
    assert audit["duplicate_input_count"] == 1
    assert audit["train_eval_input_leakage_count"] == 1


def test_current_supported_conversion() -> None:
    metrics, converted, failures = convert_current_supported_rows([_row("a")], compile_worker_count=1, timeout_seconds=5)
    assert metrics["raw_expected_output_hint_trusted"] is False
    assert converted or failures
    if converted:
        assert converted[0]["target_ir"]["op"] == "Program"
        assert "printf" not in json.dumps(converted[0]["target_ir"])


def test_future_domain_not_compiled(tmp_path: Path) -> None:
    future = _row("future", "future_domain", "future_function_call_graph", "int f(int x){return x;} int y=f(1);")
    future["language_features"]["has_function"] = True
    readiness = run_active_generation_pilot(_write_raw(tmp_path / "raw", [_row("a"), future]), tmp_path / "out", tmp_path / "records", supported_spot=1, boundary_spot=1, compile_worker_count=1)
    metrics = json.loads((tmp_path / "records" / "compiler_audit_metrics.json").read_text())
    assert metrics["future_domain_compiled_count"] == 0
    assert readiness["future_domain_compiled_count"] == 0


def test_compiler_audit_uses_real_cl(tmp_path: Path) -> None:
    run_active_generation_pilot(_write_raw(tmp_path / "raw", [_row("a")]), tmp_path / "out", tmp_path / "records", supported_spot=1, boundary_spot=0, compile_worker_count=1)
    metrics = json.loads((tmp_path / "records" / "compiler_audit_metrics.json").read_text())
    assert metrics["backend_type"] == "real_c_compiler"
    assert metrics["compiler_name"] == "cl"


def test_accepted_quarantine_rejected_split(tmp_path: Path) -> None:
    future = _row("future", "future_domain", "future_function_call_graph", "int f(int x){return x;} int y=f(1);")
    future["language_features"]["has_function"] = True
    run_active_generation_pilot(_write_raw(tmp_path / "raw", [_row("a"), future]), tmp_path / "out", tmp_path / "records", supported_spot=1, boundary_spot=1, compile_worker_count=1)
    assert (tmp_path / "out" / "accepted" / "accepted.jsonl").exists()
    assert (tmp_path / "out" / "quarantine" / "quarantine.jsonl").exists()
    assert (tmp_path / "out" / "rejected" / "rejected.jsonl").exists()


def test_active_generation_readiness_no_turing_claim(tmp_path: Path) -> None:
    readiness = run_active_generation_pilot(_write_raw(tmp_path / "raw", [_row("a")]), tmp_path / "out", tmp_path / "records", supported_spot=1, boundary_spot=0, compile_worker_count=1)
    assert readiness["turing_completeness_claimed"] is False
    assert readiness["solved_program_synthesis_claimed"] is False


def test_no_expression_oracle_import() -> None:
    text = Path("jianmu/self_learning/darwinforge/active_generation_pilot.py").read_text(encoding="utf-8")
    assert "expression_oracle" not in text


def test_no_external_api_calls() -> None:
    text = Path("jianmu/self_learning/darwinforge/active_generation_pilot.py").read_text(encoding="utf-8")
    assert "requests." not in text
    assert "urllib" not in text
    assert "openai" not in text.lower()
