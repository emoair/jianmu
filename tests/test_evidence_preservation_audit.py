from pathlib import Path

from jianmu.self_learning.darwinforge.archive_index_builder import run_forgeclean
from jianmu.self_learning.darwinforge.evidence_preservation_audit import CRITICAL_EVIDENCE_PATHS, run_evidence_preservation_audit


def test_evidence_preservation_audit_passes(tmp_path: Path) -> None:
    payload = run_evidence_preservation_audit(Path.cwd(), tmp_path)
    assert payload["all_critical_evidence_present"] is True
    assert payload["evidence_preservation_passed"] is True
    assert "records/v0_9_28_1/full_compile_50k_readiness.json" in payload["critical_evidence_paths"]


def test_critical_evidence_paths_exist() -> None:
    for rel in CRITICAL_EVIDENCE_PATHS:
        assert (Path.cwd() / rel).exists(), rel


def test_forgeclean_readiness(tmp_path: Path) -> None:
    readiness = run_forgeclean(Path.cwd(), Path("docs"), tmp_path)
    assert readiness["archive_index_generated"] is True
    assert readiness["ready_for_post_v1_0_development"] is True
    assert readiness["ready_for_official_release"] is False


def test_no_production_claim_added() -> None:
    docs = [
        Path("docs/development/POST_V1_0_DEVELOPMENT_BASELINE.md"),
        Path("docs/archive/V1_0_EVIDENCE_PRESERVATION.md"),
        Path("docs/release_prep/V1_0_EVIDENCE_INDEX.md"),
    ]
    for path in docs:
        text = path.read_text(encoding="utf-8").lower()
        assert "production ready" not in text


def test_no_expression_oracle_import() -> None:
    for rel in [
        "jianmu/self_learning/darwinforge/archive_index_builder.py",
        "jianmu/self_learning/darwinforge/development_baseline_audit.py",
        "jianmu/self_learning/darwinforge/evidence_preservation_audit.py",
    ]:
        assert "expression_oracle" not in Path(rel).read_text(encoding="utf-8")


def test_no_external_api_calls() -> None:
    forbidden = ["requests.", "urllib.request", "httpx.", "openai", "anthropic"]
    for rel in [
        "jianmu/self_learning/darwinforge/archive_index_builder.py",
        "jianmu/self_learning/darwinforge/development_baseline_audit.py",
        "jianmu/self_learning/darwinforge/evidence_preservation_audit.py",
    ]:
        text = Path(rel).read_text(encoding="utf-8")
        assert not any(item in text for item in forbidden)


def test_no_hardcoded_keyword_gate() -> None:
    text = Path("jianmu/self_learning/darwinforge/archive_index_builder.py").read_text(encoding="utf-8").lower()
    assert "keyword rejection" not in text
    assert "blacklist" not in text


def test_real_promotion_disabled() -> None:
    text = Path("jianmu/self_learning/darwinforge/archive_index_builder.py").read_text(encoding="utf-8")
    assert '"ready_for_official_release": False' in text
    assert '"release_created": False' in text
