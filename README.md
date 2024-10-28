# closure

![](https://github.com/sdingcn/closure/actions/workflows/run_test.yml/badge.svg)

This is an interpreted functional programming language
with first-class functions, recursions, and garbage collection.
Struct operations could be simulated by function closures
using the special syntax `@`, which is the origin of this language's name.
See `test/` for code examples.

## syntax

```
<comment>   := #[^\n]*\n
<integer>   := [+-]?[0-9]+
<variable>  := [a-zA-Z_][a-zA-Z0-9_]*
<intrinsic> := .void
             | .+ | .- | .* | ./ | .% | .<
             | .type  // returns an integer representation (see below) of the object's type
             | .get | .put  // integer IO (.put prints one integer per line)
<vepair>    := <variable> <expr>

<expr> := <integer>
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

+ Reference semantics (unobservable):
  variables are references (locations) of objects;
  expressions evaluate to references;
  both `letrec` and `( <callee> <expr>* )` use pass-by-reference.
+ Three immutable object types: Void (0), Int (1), Closure (2).
  Closures only include statically used variables.
+ Variables cannot be re-bound.
+ The evaluation order of `lambda` and `letrec` is left-to-right.
+ Simple periodic garbage collection with memory compaction.
+ Full tail-call optimization.
+ The language's stacks and heaps are explicit in the implementation,
  so it should be easy to support debugging, exceptions, continuations, threads, coroutines, etc.

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
