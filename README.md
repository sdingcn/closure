# closure (work in progress)

![](https://github.com/sdingcn/closure/actions/workflows/auto-test.yml/badge.svg)

## Syntax

```
<comment> := #[^\n]*\n

<integer-literal> := [+-]?[0-9]+
<variable>        := [a-z][a-zA-Z0-9_]*

<intrinsic> := .void
             | .+ | .- | .* | ./ | .% | .<
             | .type  // returns an integer representation (see below) of the object's type
                      // an object's type never changes during its lifetime
             | .get | .put  // get/put integers

<vepair> := <variable> <expr>

<expr> := <integer-literal>
        | <variable>
        | lambda ( <variable>* ) <expr>
        | letrec ( <vepair>* ) <expr>
        | if <expr> <expr> <expr>
        | { <expr>+ }
        | ( <intrinsic> <expr>* )
        | ( <expr> <expr>* )
        | @ <variable> <expr>  // access a closure's env variable
```

## Semantics

+ Reference semantics (unobservable):
  variables are references to objects;
  expressions evaluate to references of objects;
  both `letrec` and `( <expr> <expr>* )` use pass-by-reference.
+ Three object types, all immutable: `Void` (0), `Int` (1), `Closure` (2).
+ Variables cannot be re-bound.
+ The evaluation order of `lambda` and `letrec` is left-to-right.
+ Simple periodic GC without compaction; using a free-list.
+ No tail-call optimization.

## Dependency

`cmake` >= 3.28.1, a reasonable version of `make`, and `clang++` >= C++20

## Build (on Linux/macOS)

```
cd src
mkdir build
cmake -DCMAKE_BUILD_TYPE:STRING=Debug \
      -DCMAKE_CXX_COMPILER:FILEPATH=$(which clang++) \
      -S . -B build \
      -G "Unix Makefiles"
cd build
make
```
