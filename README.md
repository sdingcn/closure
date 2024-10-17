# closure (work in progress)

![](https://github.com/sdingcn/closure/actions/workflows/auto-test.yml/badge.svg)

## Syntax

```
<comment> := #[^\n]*\n

<integer-literal> := [+-]?[0-9]+
<name>            := [a-z][a-zA-Z0-9_]*
<struct-type>     := [A-Z][a-zA-Z0-9_]*

<intrinsic> := .void
             | .+ | .- | .* | ./ | .% | .<
             | .id  // returns an int rep of the object's location; can be applied to any expr
                    // an object's id is unique and never changes during the object's lifetime
             | .clone  // makes a shallow copy
             | .type  // returns an int rep of the object's type; can be applied to any expr
                      // an object's type never changes during the object's lifetime
             | .getint | .putint

<ref> := <name>
       | <expr> . <name>

<expr> := <integer-literal>
        | <ref>
        | ! <ref> <expr>
        | lambda ( <name>* ) <expr>
        | letrec ( <nepair>* ) <expr>
          where <nepair> := <name> <expr>
        | if <expr> <expr> <expr>
        | { <expr>+ }
        | struct ( <snpair>* ) <expr>
          where <snpair> := <struct-type> ( <name>* )
        | ( <intrinsic> <expr>* )
        | ( <struct-type> <expr>* )
        | ( <expr> <expr>* )
```

## Semantics

Reference semantic: all names are references to objects;
all expressions evaluate to references of objects.

Names can be re-bound by `!`.

Three basic, immutable object types: `Void`, `Int`, `Closure`.

Objects of struct types are mutable by `!`, where a struct is a tuple of names (references).

Both `letrec` and `( <callee> <expr>* )` use pass-by-reference for names.
To make a deep copy, recursively use the `.clone` intrinsic function (be aware of cycles).

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
