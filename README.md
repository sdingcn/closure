# cvm.experimental

![](https://github.com/sdingcn/cvm.experimental/actions/workflows/auto-test.yml/badge.svg)

This repository is for experimenting with interpreters, schedulers, and garbage collectors.

## Language

```
// types: void, int, str, closure
<comment>   := #[^\n]*
<variable>  := [a-zA-Z][a-zA-Z0-9_]*
<binding>   := <variable> = <expr>
<callee>    := <intrinsic>
             | <expr>
<expr>      := <int>
             | <str>
             | <variable>
             | set <variable> <expr>
             | lambda ( <variable>* ) <expr>
             | letrec ( <binding>* ) <expr>   // pass by deepcopy
             | if <expr> <expr> <expr>
             | while <expr> <expr>
             | ( <callee> <expr>* )           // pass by reference
             | [ <expr>+ ]
             | @ <variable> <expr>
             | & <variable> <expr>
<intrinsic> := .void                          // () -> void
             | .+ | .- | .* | ./ | .% | .<    // (int, int) -> int {no currying}
             | .slen                          // (str) -> int
             | .ssub                          // (str, int, int) -> str
             | .s+                            // (str, str) -> str
             | .s<                            // (str, str) -> int
             | .i->s                          // (int) -> str
             | .s->i                          // (str) -> int
             | .v? | .i? | .s? | .c?          // (any) -> int
             | .send                          // (int, int | str) -> void
             | .recv                          // (int) -> int | str | void
```

## Commands

```
cn <name> <expr>  // create a new (global) name (no duplicate)
ln                // list all defined names
dn <name>         // delete a defined name
cp <pid> <name>   // create a (background) process
lp                // list all processes (including terminated, need to be explicitly deleted)
dp <pid>          // delete a process
lm                // list messages
sd                // shutdown
```

## Dependency

`cmake` >= 3.28.1, a reasonable version of `make`, and `clang++` >= C++20

## Build and run (on Linux/macOS)

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

```
./cvm
./cvm test
```
