# Git Storm Prevention Contract

Long compiler validations must avoid creating massive untracked compiler artifacts under the worktree. Guards check artifact placement, git status latency, index locks, process counts, and records shape before and after validation.
