# v1.0.8.8.1 Compiler Integrity and OPT Display Recovery

## 1. Why this version exists

v1.0.8.8 appears to have true monotonic 8h wall-clock evidence, but human observation did not show clear MSVC `cl.exe` / `link.exe` activity. Therefore the real compiler invocation claim must be audited.

Additionally, OPT display / OPT trace appears to have been discarded and must be restored.

## 2. What this version does

- Audits v1.0.8.8 compiler invocation evidence.
- Separates frontend events from backend compiler verification.
- Records pid / returncode / artifact / stdout evidence.
- Restores OPT display / OPT trace.
- Detects antivirus / 360 interference.
- Runs a short backend validation with real `cl.exe` / `link.exe` / exe run.

## 3. What this version does not do

- It does not accept the v1.0.8.8 compiler invocation claim before audit.
- It does not claim production support completed.
- It does not claim RedQueen autonomous governance completed.
- It does not perform an official release.
- It does not complete the natural language layer.

## 4. Compiler integrity rule

A backend compiler invocation is valid only if it has source path, source sha256, `cl` command, `cl` pid, `cl` returncode, `cl` monotonic timing, object artifact, `link` command, `link` pid, `link` returncode, executable artifact, exe pid, exe returncode, expected stdout, actual stdout, and stdout match.

