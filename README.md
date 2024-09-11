# closure (work in progress)

![](https://github.com/sdingcn/closure/actions/workflows/auto-test.yml/badge.svg)

An interpreted programming language supporting suspension and resumption

## Syntax

```
// object types: void, int, str, closure
// void, int, str objects are immutable
// closure objects are mutable in the sense that their env variables can be re-bound
// variables can be re-bound
<variable>  := [a-zA-Z][a-zA-Z0-9_]*
<binding>   := <variable> = <expr>
<callee>    := <intrinsic>
             | <expr>
<expr>      := <int>
             | <str>
             | <variable>
             | set <variable> <expr>          // re-bind a variable, evaluates to void
             | lambda ( <variable>* ) <expr>
             | letrec ( <binding>* ) <expr>   // pass by reference
             | if <expr> <expr> <expr>
             | while <expr> <expr>
             | ( <callee> <expr>* )           // pass by reference
             | clone <expr>                   // TBD
             | [ <expr>+ ]
             | @check <variable> <expr>       // does a variable exist in a closure's env
             | @get <variable> <expr>         // access a variable in a closure's env
             | @set <variable> <expr>         // re-bind a variable in a closure's env
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
             | .suspend                            // (str) -> void
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
./closure // prints the usage information
./closure [-step <count>] [-time <seconds>] (<filename.closure> | <filename.state>)
Hit Ctrl+C to suspend at any time
```
