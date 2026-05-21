from __future__ import annotations

import builtins


_original_open = builtins.open


def _utf8_default_open(file, mode="r", buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
    if "b" not in mode and encoding is None:
        encoding = "utf-8"
    return _original_open(file, mode, buffering, encoding, errors, newline, closefd, opener)


builtins.open = _utf8_default_open
