# MSVC Environment Preflight Contract

The MSVC preflight must run before RedQueen stability validation when MSVC is required.

It checks `cl.exe`, `link.exe`, version command execution, Visual Studio environment variables where available, `vswhere` availability, and candidate `vcvars64.bat` paths.

If the compiler environment is not ready, validation must not start. The runner must write a clear fail-fast record and tell the user to run from x64 Native Tools Command Prompt for VS or initialize `vcvars64.bat`.
