# MSVC Frontend Filter Protocol

The v0.9.27 frontend filter invokes `cl.exe /nologo /TC /WX /Zs` on candidate C source files. `/Zs` performs syntax checking only. It does not link, does not create an executable, and does not run the program.

Frontend syntax pass is an efficiency signal only. Correctness evidence must come from full compile/link/run/stdout validation or watchdog classification.
