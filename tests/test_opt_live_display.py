from jianmu.self_learning.darwinforge.opt_live_display import format_elapsed


def test_opt_live_display_formats_elapsed() -> None:
    assert format_elapsed(3723) == "01:02:03"
