# clocalc

![](https://github.com/sdingcn/clocalc/actions/workflows/run_test.yml/badge.svg)

**Clo**sure **calc**ulus is an interpreted functional programming language.
See [test/](test/) for code examples (`*.clo`).

## syntax, semantics, and implementation

```
<comment>   := #[^\n]*\n
<integer>   := [+-]?[0-9]+  // C++ int
<string>    := "([^"] | \")*"  // see interpreter source for the supported alphabet
<variable>  := [a-zA-Z_][a-zA-Z0-9_]*
<intrinsic> := .void  // generates a Void object
             | .+ | .- | .* | ./ | .% | .< | .<= | .> | .>= | .= | ./=
             | .and | .or | .not  // no short-circuit; use "if" for short-circuit
             | .s+ | .s< | .s<= | .s> | .s>= | .s= | .s/= | .s|| | .s[] | .quote | .unquote
             | .s->i | .i->s
             | .type  // 0 for Void, 1 for Int, 2 for String, 3 for Closure
             | .eval
             | .getchar | .getint | .putstr | .flush  // IO
<vepair>    := <variable> <expr>
<expr>      := <integer>
             | <string>
             | <variable>
             | lambda ( <variable>* ) <expr>
             | letrec ( <vepair>* ) <expr>
             | if <expr> <expr> <expr>
             | { <expr>+ }  // sequenced evaluation
             | ( <intrinsic> <expr>* )
             | ( <expr> <expr>* )
             | @ <variable> <expr>  // accesses a closure's environment variable
```

+ AST-traversal based interpreter; no bytecode.
+ 4 object types: Void, Integer, String, Closure.
  Structs can be realized by closures and `@`.
+ Variables are references to objects,
  but behave like values because objects are immutable.
  Variables cannot be re-bound.
+ `letrec` and `( <callee> <expr>* )` evaluate from left to right
  and use pass-by-reference for variables.
+ Threshold-based tracing garbage collection with memory compaction.
+ Tail-call optimization,
  closure size optimization (omitting unused environment variables),
  literal object pre-allocation.
  Note: for better error messages during debugging,
  use `letrec` to rewrite tail calls to
  preserve stack frames.
+ The runtime state (including stack, heap, etc.)
  is copyable and movable, and can be executed step-by-step.
  So it's easy to suspend/resume executions.

## dependencies

The debug mode uses Clang-specific flags,
so we use Make instead of CMake.
This project was tested on Linux and macOS,
but should also compile on Windows
if you adjust the build tools.

+ `clang++` with C++20 support
+ `make`
+ `python3` (only needed for `run_test.py`)

## build and run

```
make -C src/ release
bin/clocalc <source-path>
```

`python3 run_test.py` (re-)builds the interpreter and runs all tests.
