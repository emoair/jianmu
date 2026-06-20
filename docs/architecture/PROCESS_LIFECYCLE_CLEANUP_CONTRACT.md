# Process Lifecycle Cleanup Contract

Lifecycle cleanup is an engineering hygiene contract for validation runners.

It requires subprocess, executor, trace writer, git, temp file, and post-run idle checks. Passing this contract only means the runner exits cleanly. It does not promote any runtime profile or production capability.
