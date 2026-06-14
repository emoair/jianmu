# Staged Opt-in Profile Contract

The v1.0.7 profile is explicit opt-in only. It routes requests to the already-reviewed bridge only when the staged opt-in flag is present and valid.

The default runtime profile must remain unchanged. The staged opt-in profile is not default production support and cannot set production support claims to true.
