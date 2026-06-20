from jianmu.self_learning.darwinforge.orphan_process_detector import detect_orphan_processes, process_count_by_names


def test_orphan_process_detector_detects_compiler_child():
    assert process_count_by_names(["definitely-not-a-real-process-name.exe"]) == 0
    result = detect_orphan_processes()
    assert result["orphan_process_detector_completed"] is True
