# Dry-run Rollback Contract

Rollback for v1.0.6 means disabling the shadow profile without touching the default runtime profile.

The rollback audit must show:

- the shadow profile can be closed
- default profile remains unchanged
- dry-run config is used only through explicit opt-in
- arithmetic baseline is unaffected after disabling the shadow profile
- dry-run records may remain on disk but cannot affect runtime
- production support flags do not automatically change
