# clocalc

![](https://github.com/sdingcn/clocalc/actions/workflows/run_test.yml/badge.svg)

**Clo**sure **calc**ulus is an interpreted functional programming language
with first-class functions.
Structs could be simulated by function closures
with the help of the special syntax `@`.
See `test/` for code examples.

## syntax

```
<comment>   := #[^\n]*\n
<integer>   := [+-]?[0-9]+
<variable>  := [a-zA-Z_][a-zA-Z0-9_]*
<intrinsic> := .void  // generates a Void object
             | .+ | .- | .* | ./ | .% | .< | .<= | .> | .>= | .= | ./=
             | .and | .or | .not  // no short-circuit evaluation, use "if" for short-circuit
             | .type  // returns an integer representing the object's type (see below)
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

## semantics, design, and implementation

+ AST-traversal based interpreter; no bytecode.
+ Three object types: Void (0), Int (1), Closure (2). Structs can be simulated by closures.
+ Variables are essentially references to objects,
  but they are indistinguishable from values because objects are immutable.
  Variables cannot be re-bound.
+ `letrec` and `( <callee> <expr>* )` evaluate from left to right
  and use pass-by-reference for variables.
+ Memory is managed by threshold-based tracing garbage collection with memory compaction.
+ Runtime optimizations: tail-call optimization,
  closure size optimization (omitting unused environment variables),
  literal object pre-allocation.
  Note: tail-call optimization can make stack traces in error messages hard to understand;
  to aid debugging, use additional `letrec` to rewrite tail calls.
+ The entire runtime state (including stack, heap, etc.)
  is copyable and movable, and can be executed step-by-step.
  So it's easy to realize program suspension/resumption and to support
  first-class continuations.

## dependencies

The debug mode uses Clang-specific flags;
so we use Make instead of CMake.

This project was tested on Linux and macOS,
but the C++ source file should compile on Windows
if you adjust the build tools accordingly.

+ `clang++` with C++20 support
+ `make`
+ `python3` (only needed for `run_test.py`)

## build and run

### manual

```
make -C src/ release
bin/clocalc <source-path>
```

### automatic

The following command builds the interpreter and runs all tests.

```
python3 run_test.py
```
