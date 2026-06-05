from pathlib import Path

from jianmu.self_learning.darwinforge import symbol_binding_longhaul_core as core


def _ready(wall_clock: float):
    rows = [core.build_symbol_binding_row(i) for i in range(100)]
    dataset = {"dataset_generated": True, "full_scale_attempted": True, "full_scale_completed": True}
    audit = core.audit_dataset_rows(rows, 100)
    table = core.symbol_table_metrics(rows)
    binding = core.binding_metrics(rows)
    regex = core.regex_guard_metrics(rows)
    token = core.token_metrics(rows)
    roundtrip = core.roundtrip_metrics(rows)
    equiv = core.equivalence_validation(rows)
    compiler = {"backend_claim_safe": True, "compiler_verified_correctness_rate": 1.0, "wrong_stdout_count": 0, "timeout_count": 0, "permission_error_count": 0, "cleanup_failure_count": 0, "full_compile_invocation_count": 50_000}
    accounting = core.accounting_audit(compiler, rows)
    heldout = core.heldout_metrics()
    comfort = core.comfort_zone_audit()
    cfg = core.SymbolBindingLonghaulConfig.for_scale("full")
    return core.readiness(dataset, audit, table, binding, regex, token, roundtrip, equiv, compiler, accounting, heldout, comfort, wall_clock, cfg)


def test_readiness_requires_wall_clock_6h_for_positive():
    ready = _ready(0.5)
    assert ready["recommended_claim_level"] != "symbol_binding_longhaul_positive"
    assert "wall_clock_below_minimum" in ready["blocking_issues"]


def test_readiness_non_claims_false():
    ready = _ready(6.01)
    assert ready["arbitrary_project_parsing_completed"] is False
    assert ready["memory_safety_solved"] is False
    assert ready["production_support"] is False


def test_no_expression_oracle_import():
    assert "expression_oracle" not in str(core.__dict__)


def test_no_external_api_calls():
    text = Path(core.__file__).read_text(encoding="utf-8")
    assert "requests." not in text
    assert "urllib" not in text


def test_no_hardcoded_keyword_gate():
    text = Path(core.__file__).read_text(encoding="utf-8")
    assert "keyword rejection" not in text.lower()


def test_real_promotion_disabled():
    ready = _ready(6.01)
    assert ready["ready_for_official_release"] is False

