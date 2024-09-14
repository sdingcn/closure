# closure (work in progress)

![](https://github.com/sdingcn/closure/actions/workflows/auto-test.yml/badge.svg)

## Syntax

```
<comment> := #[^\n]*\n

<integer-literal> := [+-]?[0-9]+
<string-literal>  := "([English keyboard with \ and " escaped] | [\t\n])*"
<variable>        := [a-z][a-zA-Z0-9_]*
<struct-type>     := [A-Z][a-zA-Z0-9_]*

<intrinsic> := .void
             | .+ | .- | .* | ./ | .% | .<
             | .sl | .ss | .s+ | .s<
             | .i->s | .s->i
             | .id | .type
             | .getchar | .put

<expr> := <integer-literal>
        | <string-literal>
        | <variable>
        | vset <variable> <expr>
        | lambda "(" <variable>* ")" <expr>
        | letrec "(" (<variable> <expr>)* ")" <expr>
        | if <expr> <expr> <expr>
        | while <expr> <expr>
        | "[" <expr>+ "]"
        | struct "(" (<struct-type> "(" <variable>* ")")* ")" <expr>
        | sget <expr> <variable>
        | sset <expr> <variable> <expr>
        | ( <intrinsic> <expr>* )
        | ( <struct-type> <expr>* )
        | ( <expr> <expr>* )
```

## Semantics

There are four basic object types `Void`, `Int`, `Str`, `Closure`, all of which are immutable.

New types defined using `struct` are mutable by `sset`. A `struct` is essentially a variable tuple.

Variables can be re-bound by `vset`.

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
