# v1.0.8.8.2 OPT Display Gate and True 8h Backend Validation

## 1. Why this version exists

v1.0.8.8.1 repaired backend compiler invocation integrity, but live OPT/progress display was still not visible to the user. This made it impossible to observe whether Python, cl.exe, link.exe, RedQueen, and Mirror lanes were actually progressing during long validation.

## 2. What this version does

* restores live OPT display;
* writes opt trace manifest;
* binds OPT display to backend compiler manifest;
* adds smoke test gate;
* prevents Git/IDE artifact storms;
* runs true 8h backend validation after OPT gate passes;
* preserves monotonic wall-clock timing;
* preserves compiler subprocess evidence;
* keeps artifacts outside worktree.

## 3. What this version does not do

This version does not claim production support completed, RedQueen autonomous governance completed, official release, v1.0.8.8 old compiler claim restored, or OPT display as correctness evidence.

## 4. OPT display rule

OPT display must be live, periodic, flushed, and tied to trace/manifest. It must show actual elapsed time, phase, frontend events, backend cl/link/exe counts, compiler correctness, Mirror/RedQueen state, security status, artifact root, Git storm guard status, lifecycle status, and memory/queue status.
