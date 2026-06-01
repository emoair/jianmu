from jianmu.self_learning.darwinforge.freeze_candidate_human_review import run_human_review_checklist


def test_human_review_checklist_generated(tmp_path):
    checklist = run_human_review_checklist(tmp_path)
    items = [row["item"] for row in checklist["items"]]
    assert "Claim wording review" in items
    assert "Required before v1.0 release checklist" in items
    assert checklist["human_review_checklist_completed"] is True
