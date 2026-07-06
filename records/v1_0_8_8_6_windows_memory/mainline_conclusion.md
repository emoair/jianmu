# v1.0.8.8.6 Windows Memory Attribution Audit

This version audits Windows system-level memory attribution. v1.0.8.8.5 proved Python-level streaming hygiene, but it did not explain Task Manager-wide memory pressure.

- runner_rss_peak_mb: 26.508
- runner_python_heap_peak_mb: 0.0
- process_tree_peak_rss_mb: 104.003
- system_used_memory_peak_mb: 22548.879
- system_commit_peak_mb: 28445.473
- cache_peak_mb: 3951.227
- paged_pool_peak_mb: 2661.066
- nonpaged_pool_peak_mb: 1622.402
- memory_compression_peak_mb_or_not_available: None
- top_external_memory_processes: [{'classification': 'ide', 'name': 'git.exe', 'pid': 239824, 'rss_mb': 2159.016}, {'classification': 'ide', 'name': 'git.exe', 'pid': 63380, 'rss_mb': 2116.594}, {'classification': 'ide', 'name': 'git.exe', 'pid': 17900, 'rss_mb': 2079.195}, {'classification': 'ide', 'name': 'git.exe', 'pid': 106532, 'rss_mb': 1939.27}, {'classification': 'ide', 'name': 'git.exe', 'pid': 147852, 'rss_mb': 1934.359}, {'classification': 'ide', 'name': 'git.exe', 'pid': 64864, 'rss_mb': 1899.309}, {'classification': 'ide', 'name': 'git.exe', 'pid': 203576, 'rss_mb': 1889.621}, {'classification': 'ide', 'name': 'git.exe', 'pid': 217940, 'rss_mb': 1886.762}, {'classification': 'ide', 'name': 'git.exe', 'pid': 156316, 'rss_mb': 1883.41}, {'classification': 'ide', 'name': 'git.exe', 'pid': 75380, 'rss_mb': 1872.898}]
- onedrive_activity_detected: False
- defender_activity_detected: False
- antivirus_360_activity_detected: True
- git_activity_detected: True
- ide_git_activity_detected: True
- file_cache_pressure_suspected: True
- post_run_memory_recovered: True
- unaccounted_memory_mb: 18493.649
- primary_attribution: defender_360_scan_pressure
- secondary_attributions: ['defender_360_scan_pressure', 'file_cache_standby_pressure', 'git_ide_storm']
- attribution_confidence: medium
- recommended_fixes: ['keep dataset/backend manifests streaming and bounded', 'keep compiler artifacts outside OneDrive/worktree and consider excluding temp artifact roots from real-time scanning', 'exclude transient compiler artifact roots from OneDrive/security scanner if acceptable', 'pause IDE git status scans during long validation or keep large records out of watched views']
- default_profile_unchanged: True
- real_promotion_enabled: False
- production_function_support_completed: False
- recommended_claim_level: windows_memory_pressure_explained_as_file_cache_or_external_scan
- blocking_issues: []
- required_next_run: Apply any Windows cache/scanner mitigations, then repeat memory attribution before pure heldout validation.

## Still Not Proven

- memory issue fully solved if attribution inconclusive
- pure validation on incremental dataset after memory repair
- production function support completed
- production array support completed
- production recursion support completed
- RedQueen autonomous governance completed
