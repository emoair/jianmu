# Git Command Lifecycle Contract

Git commands used by validation or release-prep helpers must run with timeout-aware subprocess handling.

The lifecycle audit checks return codes, index lock leftovers, git process leftovers, hooks presence, and credential helper waiting. It reports hooks as information and does not disable them automatically.
