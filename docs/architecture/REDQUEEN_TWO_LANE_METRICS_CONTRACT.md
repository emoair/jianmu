# RedQueen Two-lane Metrics Contract

v1.0.8.5 separates evidence into two lanes.

The real compile lane records compile, link, exe run, stdout comparison, wrong stdout, timeout, permission, cleanup, cache, duplicate, stub, and summary-only indicators. It remains the only source for real compiler correctness.

The shadow governance lane records synthetic weak signals and RedQueen scheduling response. It may influence governance scheduling, but it cannot become compiler failure evidence and cannot influence production claims.
