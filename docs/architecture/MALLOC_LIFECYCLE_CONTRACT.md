# Malloc Lifecycle Contract

Heap samples must record allocation failure branches, matched free lifecycle, and static audit flags for double-free, use-after-free, and leak-contract violations.

Passing this audit is not a full memory safety proof.
