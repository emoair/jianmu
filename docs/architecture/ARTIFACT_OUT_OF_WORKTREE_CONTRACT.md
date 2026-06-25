# Artifact Out-of-Worktree Contract

Large compiler artifacts such as `.c`, `.obj`, `.exe`, stdout, and stderr files must be written outside the Git worktree, normally under `%TEMP%\jianmu_compiler_integrity_artifacts\...`. Records may keep manifests, summaries, sample evidence packs, hashes, and artifact-root pointers.
