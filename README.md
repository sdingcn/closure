# closure (work in progress)

![](https://github.com/sdingcn/closure/actions/workflows/auto-test.yml/badge.svg)

An interpreted programming language supporting suspension and resumption

## Syntax

```
// types: void, int, str, closure
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
<intrinsic> := .void                               // () -> void
             | .+ | .- | .* | ./ | .% | .<         // (int, int) -> int
             | .strlen                             // (str) -> int
             | .strsub                             // (str, int, int) -> str
             | .str+                               // (str, str) -> str
             | .str<                               // (str, str) -> int
             | .int->str                           // (int) -> str
             | .str->int                           // (str) -> int
             | .void? | .int? | .str? | .closure?  // (any) -> int
             | .getline                            // () -> str
             | .put                                // (str) -> void
             | .save                               // (str) -> void
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
./closure test
./closure <filename.closure>
./closure <filename.state>
```
