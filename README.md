# closure

![](https://github.com/sdingcn/closure/actions/workflows/run_test.yml/badge.svg)

This is an interpreted functional programming language
with first-class functions.
Structs could be simulated by function closures
with the help of the special syntax `@`.
See `test/` for code examples.

## syntax

```
<comment>   := #[^\n]*\n
<integer>   := [+-]?[0-9]+
<variable>  := [a-zA-Z_][a-zA-Z0-9_]*
<intrinsic> := .void  // generate a Void object
             | .+ | .- | .* | ./ | .% | .<
             | .type  // returns an integer representing the object's type (see below)
             | .get | .put  // integer IO (.put prints one integer per line)
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

## semantics and implementation details

+ Three object types: Void (0), Int (1), Closure (2).
+ Variables are essentially references,
  but they are indistinguishable from values because objects are immutable.
  Variables cannot be re-bound.
+ `letrec` and `( <callee> <expr>* )` evaluate from left to right
  and use pass-by-reference for variables.
+ Optimizations: garbage collection with memory compaction, tail-call optimization,
  closure environment optimization (including only statically used free variables).
+ The runtime state is copyable, movable, and can be executed step-by-step.
  You can use the interpreter as a library to realize program suspension and resumption.
  It's also straightforward to add first-class continuations to the language.

## dependencies

+ `cmake` >= 3.28.1
+ a C++20 compiler (e.g. `clang++`) and a build system (e.g. `make`)
+ `python3` (only needed for `run_test.py`)

## build (on Linux/macOS) and run

### manual

```
mkdir build
cmake -DCMAKE_BUILD_TYPE:STRING=Release -S src -B build
cmake --build build
```

```
build/closure <source-path>
```

### automatic

The following command removes previous builds (if any), builds the interpreter, and runs all tests.

```
python3 run_test.py
```
