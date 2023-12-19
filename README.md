# exprscript

![](https://github.com/sdingcn/expr/actions/workflows/auto-test.yml/badge.svg)

ExprScript is a dynamically typed functional programming language.

#### Small core

| Language feature | Implementation |
| --- | --- |
| Structures / Records ([test/binary-tree.expr](test/binary-tree.expr)) | Closures |
| Object-oriented programming ([test/oop.expr](test/oop.expr)) | Closures and dynamically scoped variables |
| Coroutines ([test/coroutines.expr](test/coroutines.expr)) | Continuations |
| Lazy evaluation ([test/lazy-evaluation.expr](test/lazy-evaluation.expr)) | Zero-argument functions |
| Multi-stage evaluation ([test/multi-stage.expr](test/multi-stage.expr)) | `eval` |

#### Full-precision rational numbers

[test/average.expr](test/average.expr)

#### Interactions with Python

[src/interaction-examples.py](src/interaction-examples.py)

## Syntax and semantics

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
  | .void? | .num? | .str? | .clo? | .cont?  // object type testers
  | .getline | .put
  | .call/cc                                 // call with current continuation
  | .eval | .exit
  | .py                                      // call a py function from es
  | .reg                                     // register an es function to be used in py
<binding> :=
    <variable> = <expr>
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
  | ( <callee> <expr>* )
  | [ <expr>+ ]                              // sequence evaluation
  | @ <query-body>                           // whether a var is defined
  | & <lexical-variable> <expr>              // access a lex var in a closure's env
```

Supported object types: Void, Number, String, Closure, Continuation.
Functions are not curried by default.
Objects are immutable.
Variables are references to objects and are immutable once bound.
Tail call optimization and garbage collection are supported.
Some runtime information will be written to `stderr`.

## Dependency and usage

Python >= 3.9

```
python3 src/exprscript.py <file>
python3 test.py
```
