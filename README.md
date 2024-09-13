# closure (work in progress)

![](https://github.com/sdingcn/closure/actions/workflows/auto-test.yml/badge.svg)

## Syntax

```
<int-literal> := [+-]?[0-9]+
<str-literal> := English keyboard + [\t\n]

<variable>        := [a-zA-Z][a-zA-Z0-9_]*
<struct-type>     := [A-Z][a-zA-Z0-9_]*

<variable-binding>    := <variable> <expr>
<struct-type-binding> := <struct-type> (<variable>*)

<callee> := <expr> | <intrinsic> | <struct-type>

<expr> := <int-literal>
        | <str-literal>
        | <variable>
        | set <variable> <expr>                  // re-bind a variable, evaluating to Void
        | lambda ( <variable>* ) <expr>
        | letrec ( <variable-binding>* ) <expr>
        | if <expr> <expr> <expr>
        | while <expr> <expr>
        | [ <expr>+ ]                            // sequenced evaluation
        | struct ( <type-binding>* ) <expr>
        | ( <callee> <expr>* )
        | @get <variable> <expr>                 // struct field reading
        | @set <variable> <expr>                 // struct field modification, evaluating to Void

<intrinsic> := void                   // () -> Void
             | + | - | * | / | % | <  // (Int, Int) -> Int
             | sl                     // (Str) -> Int
             | ss                     // (Str, Int, Int) -> Str
             | s+                     // (Str, Str) -> Str
             | s<                     // (Str, Str) -> Int
             | i->s                   // (Int) -> Str
             | s->i                   // (Str) -> Int
             | id                     // (Any) -> Int
             | type                   // (Any) -> Str
             | getchar                // () -> Str
             | put                    // (Str) -> Void
```

## Semantics

There are four basic object types `Void`, `Int`, `Str`, `Closure`, all of which are immutable.

New types defined using `struct` are mutable by `@set`. A `struct` is essentially a variable tuple.

Variables can be re-bound by `set`.

Both `letrec` and `( <callee> <expr>* )` use pass-by-reference for variables.

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

## Interpreter commands

TODO: basically making a reversible debugger
