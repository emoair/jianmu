# RedQueen Runner Shutdown Contract

RedQueen runners must leave no non-daemon worker threads, multiprocessing children, compiler subprocesses, generated executable processes, git subprocesses, or open manifest handles after completion.

The runner must write records before exit and then pass the post-run idle sentinel.
