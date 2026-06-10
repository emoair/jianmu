# Windows Records Write Isolation Contract

Controlled review treats historical records as read-only. New review output must use a versioned records directory or temporary paths.

Audit helpers should use atomic writes for review artifacts when practical. Tests that generate files should prefer `tmp_path` and must not rely on writing old historical records directories.

The v1.0.6 transient Windows failure is classified as test-side historical records write risk unless reproduced in current review outputs.
