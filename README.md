# cvm

![](https://github.com/sdingcn/closure/actions/workflows/auto-test.yml/badge.svg)

Closure virtual machine, for a dynamically-typed function language closure

## Language

```
<comment> :=
    #.*\n
<number> :=                                  // integers, decimals, fractions
    [+-]?0
  | [+-]?[1-9][0-9]*
  | [+-]?0\.[0-9]*[1-9]
  | [+-]?[1-9][0-9]*\.[0-9]*[1-9]
  | [+-]?0/[1-9][0-9]*
  | [+-]?[1-9][0-9]*/[1-9][0-9]*
<string> :=
    "( [^"\] | \" | \\ | \t | \n )*"         // charset is English keyboard
<lexical-variable> :=
    [a-z][a-zA-Z0-9_]*                       // lexically scoped var
<dynamic-variable> :=
    [A-Z][a-zA-Z0-9_]*                       // dynamically scoped var
<variable> :=
    <lexical-variable>
  | <dynamic-variable>
<intrinsic> :=
    .void
  | .+ | .- | .* | ./ | .% | .floor | .ceil
  | .< | .<= | .> | .>=
  | .== | .!=
  | .and | .or | .not                        // use 0/1 as Booleans
  | .strlen | .strcut | .str+ | .strnum
  | .strquote                                // "abc" -> "\"abc\""
  | .str< | .str<= | .str> | .str>=
  | .str== | .str!=
  | .void? | .num? | .str? | .clo? | .cont?  // object type query
                                             // 5 types of objects; all immutable
  | .getline | .put                          // read/write from/to stdin/stdout
                                             // some runtime info is printed to stderr
  | .call/cc                                 // call with current continuation
  | .eval | .exit
<binding> :=
    <variable> = <expr>                      // vars are references to objects
                                             // vars cannot be re-bound
                                             // objects are managed by garbage collection
<callee> :=
    <intrinsic>
  | <expr>
<query-body> :=
    <dynamic-variable>                       // is var defined here?
  | <lexical-variable> <expr>                // is var defined in the closure's env?
<expr> :=
    <number>
  | <string>
  | <variable>
  | lambda ( <variable>* ) { <expr> }        // anonymous functions
  | letrec ( <binding>* ) { <expr> }         // mutually recursive bindings
  | if <expr> then <expr> else <expr>
  | ( <callee> <expr>* )                     // calls are not curried
                                             // tail call optimization is applied
  | [ <expr>+ ]                              // sequence evaluation
  | @ <query-body>                           // whether a var is defined
  | & <lexical-variable> <expr>              // access a lex var in a closure's env
```

## Dependency and usage

Python >= 3.9

```
python3 src/closure.py <file>
python3 test.py
```

## (TODO) Rewrite using C++

## (TODO) Support an enhanced REPL: call/cc-based multi-tasking
