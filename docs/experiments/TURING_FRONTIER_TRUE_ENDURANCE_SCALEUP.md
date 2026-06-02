# Turing Frontier True Endurance Scaleup

v0.9.26 opened the Turing-substrate experimental frontier, but its longhaul run did not satisfy the hard wall-clock rule. v0.9.26.1 reruns the frontier with a true endurance protocol: wall_clock_min_hours is 12, sample completion cannot end the run early, and any run below 12 hours is partial.

The version adds frontier failure taxonomy for unbounded while, recursion, state growth, counter-machine transitions, and watchdog/timeout classification. RedQueen repair assignments target the dominant failure categories through required features and difficulty changes while keeping unsupported frontier samples out of current_supported production boundaries.

This remains finite experimental evidence. It is not a formal proof of Turing completeness, not production support, not recursion production support, and not a v1.0 release.
