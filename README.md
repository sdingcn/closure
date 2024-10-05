# closure (work in progress)

![](https://github.com/sdingcn/closure/actions/workflows/auto-test.yml/badge.svg)

## Syntax

```
<comment> := #[^\n]*\n

<integer-literal> := [+-]?[0-9]+
<string-literal>  := see the interpreter source
<variable>        := [a-z][a-zA-Z0-9_]*
<field>           := [a-z][a-zA-Z0-9_]*
<struct-type>     := [A-Z][a-zA-Z0-9_]*

<intrinsic> := .void
             | .+ | .- | .* | ./ | .% | .<
             | .sl | .ss | .s+ | .s<
             | .i->s | .s->i
             | .id  // returns an int representation of the object's location; can be applied to any expr
                    // an object's id is unique and never changes during the object's lifetime
             | .clone  // makes a shallow copy
             | .type  // returns a string representation of the object's type; can be applied to any expr
                      // an object's type never changes during the object's lifetime
             | .getchar | .put

<expr> := <integer-literal>
        | <string-literal>
        | <variable>
        | vset <variable> <expr>
        | lambda ( <variable>* ) <expr>
        | letrec ( <vepair>* ) <expr>
          where <vepair> := <variable> <expr>
        | if <expr> <expr> <expr>
        | while <expr> <expr>
        | { <expr>+ }
        | struct ( <sfpair>* ) <expr>
          where <sfpair> := <struct-type> ( <field>* )
        | sget <expr> <field>
        | sset <expr> <field> <expr>
        | ( <intrinsic> <expr>* )
        | ( <struct-type> <expr>* )
        | ( <expr> <expr>* )
```

## Semantics

Reference semantic: all variables and fields are references to objects; all expressions evaluate to references of objects.

Variables can be re-bound by `vset`.

Four basic, immutable object types: `Void`, `Int`, `Str`, `Closure`.

Objects of struct types are mutable by `sset`, where a struct is essentially a tuple of fields (references).

Both `letrec` and `( <callee> <expr>* )` use pass-by-reference for variables. To make a deep copy, recursively use the `.clone` intrinsic function (be aware of cycles).

Garbage collection: do a simple periodic GC and don't do compaction.

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

## Use

Open the internal state manipulation to the command line (so it's easy to debug the code, save the state, etc.)?
