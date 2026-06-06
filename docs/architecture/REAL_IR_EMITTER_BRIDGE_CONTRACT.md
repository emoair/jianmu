# Real IR Emitter Bridge Contract

The bridge must build real ExtendedIR objects before emitting C. It may reuse ForgeFrontier semantics as input guidance, but it must not call the ForgeFrontier validation template renderer as the final emitter.

The minimal supported experimental subset is pure int functions, fixed int arrays, a function consuming an array, and bounded structural recursion examples such as factorial.

All bridge evidence remains experimental until it is integrated into the production profile through a separate review.

