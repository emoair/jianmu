# Sandboxed File IO Contract

File IO samples are limited to temporary sandbox working directories. Absolute paths, parent traversal, user directories, system directories, remove, rename, delete, shell execution, and network access are outside this contract.

Sandboxed file IO is diagnostic only and not production file IO support.
