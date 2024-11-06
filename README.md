# clocalc

![](https://github.com/sdingcn/clocalc/actions/workflows/run_test.yml/badge.svg)

**Clo**sure **calc**ulus is an interpreted functional programming language.
See `test/*.clo` for code examples.

## syntax

```
<comment>   := #[^\n]*\n
<integer>   := [+-]?[0-9]+  // C++ int
<variable>  := [a-zA-Z_][a-zA-Z0-9_]*
<intrinsic> := .void  // generates a Void object
             | .+ | .- | .* | ./ | .% | .< | .<= | .> | .>= | .= | ./=
             | .and | .or | .not  // no short-circuit; use "if" for short-circuit
             | .type  // returns an integer; 0 for Void, 1 for Int, 2 for Closure
             | .get | .put | .flush  // integer IO
<vepair>    := <variable> <expr>
<expr>      := <integer>
             | <variable>
             | lambda ( <variable>* ) <expr>
             | letrec ( <vepair>* ) <expr>
             | if <expr> <expr> <expr>
             | { <expr>+ }  // sequenced evaluation
             | ( <intrinsic> <expr>* )
             | ( <expr> <expr>* )
             | @ <variable> <expr>  // accesses a closure's environment variable
```

## semantics and implementation

+ AST-traversal based interpreter; no bytecode.
+ Three object types: Void, Int, Closure. Structs can be simulated by closures.
+ Variables are references to objects,
  but they are indistinguishable from values because objects are immutable.
  Variables cannot be re-bound.
+ `letrec` and `( <callee> <expr>* )` evaluate from left to right
  and use pass-by-reference for variables.
+ Threshold-based tracing garbage collection with memory compaction.
+ Tail-call optimization,
  closure size optimization (omitting unused environment variables),
  literal (Int) object pre-allocation.
  Note: for debugging, use `letrec` to rewrite tail calls to get clear
  stack traces in error messages.
+ The entire runtime state (including stack, heap, etc.)
  is copyable and movable, and can be executed step-by-step.
  So it's easy to suspend/resume executions and to support
  first-class continuations.

## dependencies

The debug mode uses Clang-specific flags,
so we use Make instead of CMake.
This project was tested on Linux and macOS,
but the C++ source file should compile on Windows
if you adjust the build tools.

+ `clang++` with C++20 support
+ `make`
+ `python3` (only needed for `run_test.py`)

## build and run

```
make -C src/ release
bin/clocalc <source-path>
```

Use `python3 run_test.py` to build the interpreter and run all tests.
