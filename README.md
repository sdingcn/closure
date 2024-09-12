# closure (work in progress)

![](https://github.com/sdingcn/closure/actions/workflows/auto-test.yml/badge.svg)

## Syntax

```
<int-literal> := [+-]?0 | [+-]?[1-9][0-9]
<str-literal> := keyboard?

<variable> := [a-zA-Z][a-zA-Z0-9_]*
<type>     := [A-Z][a-zA-Z0-9_]*

<variable-binding> := <variable> = <expr>
<type-binding>     := <type> = (<variable>*)

<expr> := <int>
        | <str>
        | <variable>
        | set <variable> <expr>                  // re-bind a variable, evaluates to void
        | lambda ( <variable>* ) <expr>
        | letrec ( <variable-binding>* ) <expr>
        | if <expr> <expr> <expr>
        | while <expr> <expr>
        | [ <expr>+ ]                            // sequenced evaluation
        | struct ( <type-binding>* ) <expr>
        | ( <intrinsic> <expr>* )                // intrinsic call
        | ( <variable> <expr>* )                 // user-defined function call
        | ( <type> <expr>* )                     // constructor call
        | @get <variable> <expr>                 // field reading
        | @set <variable> <expr>                 // field modification

<intrinsic> := void                   // () -> void
             | + | - | * | / | % | <  // (int, int) -> int
             | sl                     // (str) -> int
             | ss                     // (str, int, int) -> str
             | s+                     // (str, str) -> str
             | s<                     // (str, str) -> int
             | i->s                   // (int) -> str
             | s->i                   // (str) -> int
             | is                     // (struct, struct) -> int
             | type                   // (any) -> str
             | getchar                // () -> str
             | put                    // (str) -> void
```

## Semantics

There are five basic object types `Void`, `Int`, `Str`, `Closure`, all of which are immutable.

New types defined using `struct` are mutable in the sense that their fields can be re-bound by `@set`.

Variables can be re-bound by `set`.

Both `letrec` and `(<callee> <expr>*)` (intrinsic / user-defined function / constructor call) have variables pass-by-reference.

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
