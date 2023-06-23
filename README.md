# exprscript

[中文 README](README-CN.md)

![](https://github.com/sdingcn/expr/actions/workflows/auto-test.yml/badge.svg)

ExprScript is a dynamically typed functional programming language.

+ Small language core, rich language features

| Feature | Implementation |
| --- | --- |
| Structures / Records ([test/binary-tree.expr](test/binary-tree.expr)) | Closures |
| Object-oriented programming ([test/oop.expr](test/oop.expr)) | Closures and dynamically scoped variables |
| Coroutines ([test/coroutines.expr](test/coroutines.expr)) | Continuations |
| Lazy evaluation ([test/lazy-evaluation.expr](test/lazy-evaluation.expr)) | Zero-argument functions |
| Multi-stage evaluation ([test/multi-stage.expr](test/multi-stage.expr)) | `eval` |

+ Native support for full-precision rational numbers

```
$ cat test/average.expr
letrec (
  sum = (.+ 100/11 61 +15/7 1.355 -41.06)
) {
  (./ sum 5)
}
$ python3 src/exprscript.py test/average.expr
500943/77000
```

+ Natural interactions with Python

[src/call-python-from-exprscript.py](src/call-python-from-exprscript.py)

[src/call-exprscript-from-python.py](src/call-exprscript-from-python.py)

## dependencies

Python >= 3.9

## syntax and semantics

```
<comment> := #.*?\n
<head-nonzero> := [1-9][0-9]*
<tail-nonzero> := [0-9]*[1-9]
<number> := [+-]?0 | [+-]?<head-nonzero>
          | [+-]?0.<tail-nonzero> | [+-]?<head-nonzero>.<tail-nonzero>
          | [+-]?0/<head-nonzero> | [+-]?<head-nonzero>/<head-nonzero>
<string> := "( [^"\] | \" | \\ | \t | \n )*" // charset is English keyboard
<lexical-variable> := [a-z][a-zA-Z0-9_]*         // lexically scoped variable
<dynamic-variable> := [A-Z][a-zA-Z0-9_]*         // dynamically scoped variable
<variable> := <lexical-variable> | <dynamic-variable>
<intrinsic> := .void
             | .+ | .- | .* | ./ | .% | .floor | .ceil
             | .< | .<= | .> | .>= | .== | .!=
             | .and | .or | .not             // for simplicity use numbers as Booleans
             | .strlen | .strcut | .str+ | .strnum | .strquote
             | .str< | .str<= | .str> | .str>= | .str== | .str!= 
             | .getline | .put
             | .void? | .num? | .str? | .clo? | .cont?
             | .call/cc | .eval | .exit
             | .py | .reg                    // Python interaction
<binding> := <variable> = <expr>
<callee> := <intrinsic> | <expr>
<query-body> := <dynamic-variable>           // Is it defined here?
              | <lexical-variable> <expr>    // Is it defined in the closure's environment?
<expr> := <number> | <string> | <variable>
        | lambda ( <variable>* ) { <expr> }
        | letrec ( <binding>* ) { <expr> }
        | if <expr> then <expr> else <expr>
        | ( <callee> <expr>* )
        | [ <expr>+ ]                        // sequence evaluation
        | @ <query-body>                     // query whether a variable is defined
        | & <lexical-variable> <expr>        // access a variable in a closure's env
```

Supported object types: Void, Number, String, Closure, Continuation.
Functions are not curried by default.
Objects are immutable.
Variables are references to objects and are immutable once bound.
Garbage collection (GC) runs when 80% of the reserved heap space is occupied,
and if GC cannot reduce the occupancy to be < 80%, the reserved heap space will grow.
The evaluation result of the entire program is printed to `stdout`.

## usage

+ `python3 src/exprscript.py <file>` runs code in `<file>`.
+ `python3 test.py` runs all tests (see [test.py](test.py) for inputs/outputs for each test program).
