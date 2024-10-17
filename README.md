# closure (work in progress)

![](https://github.com/sdingcn/closure/actions/workflows/auto-test.yml/badge.svg)

## Syntax

```
<comment> := #[^\n]*\n

<integer-literal> := [+-]?[0-9]+
<variable>        := [a-z][a-zA-Z0-9_]*

<intrinsic> := .void
             | .+ | .- | .* | ./ | .% | .<
             | .type  // returns an int rep of the object's type; can be applied to any expr
                      // an object's type never changes during the object's lifetime
             | .getint | .putint

<expr> := <integer-literal>
        | <variable>
        | lambda ( <variable>* ) <expr>
        | letrec ( <vepair>* ) <expr>
          where <vepair> := <variable> <expr>
        | if <expr> <expr> <expr>
        | { <expr>+ }
        | ( <intrinsic> <expr>* )
        | ( <expr> <expr>* )
        | @ <variable> <expr>
```

## Semantics

Reference semantic (unobservable): all names are references to objects;
all expressions evaluate to references of objects.

Three basic, immutable object types: `Void`, `Int`, `Closure`.

Variables cannot be re-bound.

Both `letrec` and `( <callee> <expr>* )` use pass-by-reference for names.

Garbage collection: do a simple periodic GC and don't do compaction; maybe use a free list.

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
