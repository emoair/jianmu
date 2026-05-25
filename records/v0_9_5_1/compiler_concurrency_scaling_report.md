# Compiler Concurrency Scaling Report

- workers=4: sps=15.863275, stable=True, p99=282.7496, timeouts=0, compile_failures=0, runtime_failures=0, process_spawn_errors=0, trace_write_errors=0
- workers=8: sps=26.096334, stable=True, p99=410.6114, timeouts=0, compile_failures=0, runtime_failures=0, process_spawn_errors=0, trace_write_errors=0
- workers=16: sps=29.775972, stable=True, p99=684.0464, timeouts=0, compile_failures=0, runtime_failures=0, process_spawn_errors=0, trace_write_errors=0
- workers=32: sps=28.520208, stable=True, p99=1521.6372, timeouts=0, compile_failures=0, runtime_failures=0, process_spawn_errors=0, trace_write_errors=0
- workers=64: sps=17.949307, stable=True, p99=12042.1378, timeouts=0, compile_failures=0, runtime_failures=0, process_spawn_errors=0, trace_write_errors=0
- workers=128: sps=25.788933, stable=True, p99=8902.7327, timeouts=0, compile_failures=0, runtime_failures=0, process_spawn_errors=0, trace_write_errors=0
- workers=256: sps=20.570908, stable=False, p99=22763.4463, timeouts=219, compile_failures=165, runtime_failures=219, process_spawn_errors=0, trace_write_errors=0
- workers=512: sps=None, stable=False, p99=None, timeouts=0, compile_failures=0, runtime_failures=0, process_spawn_errors=0, trace_write_errors=0

Recommended claim level: high_concurrency_stable
