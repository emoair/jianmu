# Windows Memory Attribution Audit

## 1. Why this version exists

v1.0.8.8.5 repaired Python-level streaming and queue memory issues, but Windows Task Manager still appeared to show high memory usage without an obvious source. This version audits system-level memory attribution.

## 2. What this version does

- distinguishes Python heap from Windows process tree memory
- captures top process private bytes / working set
- captures system commit / cache / pool / memory compression
- classifies Git / IDE / OneDrive / Defender / 360 / MSVC activity
- tracks artifact file churn and cache pressure
- records before/during/after memory timelines
- runs a short workload replay
- produces an attribution report

## 3. What this version does not do

It does not claim production support completed, RedQueen autonomous governance completed, official release, memory issue fully solved if attribution remains unknown, or system cache equals Python leak.
